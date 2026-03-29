"""
OgaDoctor Backend Server - Video Consultation System
====================================================
Connects Botpress to Supabase with Twilio Video integration

Deploy to: Railway.app or Render.com
Run locally: python backend.py
"""

from flask import Flask, request, jsonify
from supabase import create_client
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from datetime import datetime
import os
import requests
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# ============================================================================
# CONFIGURATION
# ============================================================================

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Twilio credentials (for video)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_API_KEY = os.getenv("TWILIO_API_KEY", "")
TWILIO_API_SECRET = os.getenv("TWILIO_API_SECRET", "")

# OpenAI credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def assign_to_available_doctor():
    """Find an available doctor and return their ID and phone"""
    try:
        doctors = supabase.table('doctors')\
            .select('*')\
            .eq('is_online', True)\
            .eq('status', 'active')\
            .execute().data
        
        if doctors and len(doctors) > 0:
            return doctors[0]['id'], doctors[0]['phone_number']
        else:
            return None, None
    except Exception as e:
        print(f"❌ Error finding doctor: {e}")
        return None, None

def assign_to_available_pharmacist():
    """Find an available pharmacist and return their ID and phone"""
    try:
        pharmacists = supabase.table('pharmacists')\
            .select('*')\
            .eq('is_online', True)\
            .eq('status', 'active')\
            .execute().data
        
        if pharmacists and len(pharmacists) > 0:
            return pharmacists[0]['id'], pharmacists[0]['phone_number']
        else:
            return None, None
    except Exception as e:
        print(f"❌ Error finding pharmacist: {e}")
        return None, None

def determine_priority(severity):
    """Determine consultation priority based on severity"""
    severity_lower = str(severity).lower()
    
    if any(word in severity_lower for word in ['severe', 'critical', 'emergency', 'urgent', 'very strong']):
        return 'URGENT'
    elif any(word in severity_lower for word in ['moderate', 'concerning', 'strong']):
        return 'MODERATE'
    else:
        return 'LOW'

def run_ai_diagnosis(symptoms, severity, duration):
    """Run AI diagnosis using OpenAI GPT-4"""
    try:
        print(f"🤖 AI Diagnosis starting...")
        print(f"   Symptoms: {symptoms}")
        print(f"   Severity: {severity}")
        print(f"   Duration: {duration}")
        
        if not openai_client:
            print("❌ OpenAI client not initialized!")
            print(f"   OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
            return "AI unavailable - OpenAI not configured", "Please consult doctor"
        
        print("✅ OpenAI client initialized")
        
        prompt = """You are a clinical decision support system for a Nigerian community pharmacy.
Your role:
1. Provide a likely diagnosis based on symptoms
2. Recommend appropriate OTC medications available in Nigeria
3. Include dosage instructions
4. Flag if patient should see a doctor instead

Format your response EXACTLY like this:
DIAGNOSIS: [Your assessment]
MEDICATIONS:
1. [Drug name] - [Dosage] - [Duration]
2. [Drug name] - [Dosage] - [Duration]
ADVICE: [Any additional care instructions]
RED FLAGS: [If patient should see doctor instead of self-treating]

Be practical and only suggest medications commonly available in Nigerian pharmacies."""

        print("🔄 Calling OpenAI API...")
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Patient Information:\nSymptoms: {symptoms}\nSeverity: {severity}\nDuration: {duration}\n\nPlease provide diagnosis and treatment recommendations."}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        print("✅ OpenAI API responded")
        
        ai_response = response.choices[0].message.content
        
        print(f"📝 AI Response length: {len(ai_response)} characters")
        
        # Parse AI response
        diagnosis = ""
        medications = ""
        
        if "DIAGNOSIS:" in ai_response:
            diagnosis_match = ai_response.split("DIAGNOSIS:")[1].split("MEDICATIONS:")[0].strip()
            diagnosis = diagnosis_match
        
        if "MEDICATIONS:" in ai_response:
            meds_match = ai_response.split("MEDICATIONS:")[1]
            if "ADVICE:" in meds_match:
                meds_match = meds_match.split("ADVICE:")[0]
            elif "RED FLAGS:" in meds_match:
                meds_match = meds_match.split("RED FLAGS:")[0]
            medications = meds_match.strip()
        
        if not diagnosis:
            diagnosis = ai_response
        if not medications:
            medications = ai_response
        
        print(f"✅ AI Diagnosis completed successfully")
        print(f"   Diagnosis: {diagnosis[:50]}...")
        print(f"   Medications: {medications[:50]}...")
        
        return diagnosis, medications
        
    except Exception as e:
        print(f"❌ AI Diagnosis error: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return "AI analysis unavailable", "Doctor will assess manually"
def send_whatsapp_notification(phone_number, message):
    """Send WhatsApp notification via Twilio"""
    try:
        # Format phone number for WhatsApp (must include country code)
        
        # Remove any spaces or special characters
        clean_number = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        print(f"🔍 Processing phone: '{phone_number}' → cleaned: '{clean_number}' (length: {len(clean_number)})")
        
        # Handle different phone number formats
        if clean_number.startswith('+44'):
            # Explicitly UK: +447062862607
            whatsapp_number = f'whatsapp:{clean_number}'
            print(f"   → Matched: UK (explicit +44)")
        
        elif clean_number.startswith('+234'):
            # Explicitly Nigerian: +2347062862607
            whatsapp_number = f'whatsapp:{clean_number}'
            print(f"   → Matched: Nigerian (explicit +234)")
        
        elif clean_number.startswith('+'):
            # Other country with +
            whatsapp_number = f'whatsapp:{clean_number}'
            print(f"   → Matched: International (+)")
        
        elif clean_number.startswith('00'):
            # 00234... format → +234...
            whatsapp_number = f'whatsapp:+{clean_number[2:]}'
            print(f"   → Matched: 00 prefix")
        
        elif clean_number.startswith('0') and len(clean_number) >= 10:
            # Nigerian number with 0: 07062862607 → +2347062862607
            # (Assuming Nigerian by default since that's your primary market)
            whatsapp_number = f'whatsapp:+234{clean_number[1:]}'
            print(f"   → Matched: Nigerian number (0 prefix)")
        
        elif clean_number.startswith('234'):
            # 2347062862607 → +2347062862607
            whatsapp_number = f'whatsapp:+{clean_number}'
            print(f"   → Matched: Nigerian (starts with 234)")
        
        elif clean_number.startswith('44') and len(clean_number) >= 12:
            # 447062862607 → +447062862607
            whatsapp_number = f'whatsapp:+{clean_number}'
            print(f"   → Matched: UK (starts with 44)")
        
        elif len(clean_number) == 10 and clean_number[0] in '7890':
            # 10 digit number starting with 7/8/9/0
            # ASSUME NIGERIAN (your primary market)
            whatsapp_number = f'whatsapp:+234{clean_number}'
            print(f"   → Matched: Nigerian (10 digits, assumed)")
        
        elif len(clean_number) == 11 and clean_number[0] in '7890':
            # 11 digit number starting with 7/8/9/0
            # ASSUME NIGERIAN without the 0
            whatsapp_number = f'whatsapp:+234{clean_number[1:] if clean_number[0] == "0" else clean_number}'
            print(f"   → Matched: Nigerian (11 digits)")
        
        else:
            # Assume it already has country code, just missing +
            whatsapp_number = f'whatsapp:+{clean_number}'
            print(f"   → Matched: Default (assume has country code)")
        
        print(f"📱 Sending WhatsApp to {whatsapp_number}")
        
        # Send via Twilio
        twilio_message = twilio_client.messages.create(
            from_='whatsapp:+14155238886',  # Twilio WhatsApp sandbox number
            to=whatsapp_number,
            body=message
        )
        
        print(f"✅ WhatsApp sent! SID: {twilio_message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp send failed: {e}")
        return False
    # TODO: Implement WhatsApp Business API

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OgaDoctor Backend - Video System',
        'version': '2.1',
        'features': [
            'Encrypted video consultations',
            'Botpress integration',
            'Paystack payments',
            'AI-powered diagnosis (post-payment)',
            'Doctor and Pharmacist assignment'
        ]
    })

@app.route('/webhook/botpress', methods=['POST'])
def botpress_webhook():
    """
    Receive patient consultation data from Botpress
    NOTE: AI diagnosis NOT included here - it runs AFTER payment
    
    Expected JSON:
    {
        "patient_name": "Amaka Obi",
        "patient_phone": "+234803XXXXXXX",
        "symptoms": "Headache and fever",
        "severity": "Strong",
        "duration": "2 days",
        "consultation_type": "doctor"
    }
    """
    try:
        data = request.json
        print(f"📥 Received from Botpress: {data}")
        
        # Extract data
        patient_name = data.get('patient_name', 'Unknown')
        patient_phone = data.get('patient_phone')
        symptoms = data.get('symptoms')
        severity = data.get('severity', 'moderate')
        duration = data.get('duration', 'Not specified')
        consultation_type = data.get('consultation_type', 'doctor')
        
        # Validate
        if not patient_phone or not symptoms:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: patient_phone and symptoms'
            }), 400
        
        # Determine priority
        priority = determine_priority(severity)
        
        # Determine fees
        if consultation_type == 'pharmacist':
            consultation_fee = 1000
            provider_payout = 670  # 67%
            platform_commission = 330  # 33%
        else:  # doctor
            consultation_fee = 1500
            provider_payout = 1000  # 67%
            platform_commission = 500  # 33%
        
        # Create or get user
        user_result = supabase.table('users')\
            .select('*')\
            .eq('phone_number', patient_phone)\
            .execute()
        
        if user_result.data and len(user_result.data) > 0:
            user_id = user_result.data[0]['id']
            print(f"✅ Found existing user: {user_id}")
        else:
            new_user = supabase.table('users').insert({
                'phone_number': patient_phone,
                'name': patient_name,
                'total_consultations': 0,
                'total_spent': 0
            }).execute()
            user_id = new_user.data[0]['id']
            print(f"✅ Created new user: {user_id}")
        
        # Create consultation WITHOUT AI diagnosis (will be added after payment)
        consultation_data = {
            'patient_name': patient_name,
            'patient_phone': patient_phone,
            'user_id': user_id,
            'symptoms': symptoms,
            'severity': severity,
            'duration': duration,
            'priority': priority,
            'status': 'pending',
            'payment_status': 'unpaid',
            'consultation_fee': consultation_fee,
            'ai_diagnosis': '',  # Will be filled after payment
            'ai_drug_recommendations': '',  # Will be filled after payment
            'platform_commission': platform_commission,
            'provider_payout': provider_payout,
            'created_at': datetime.now().isoformat()
        }
        
        # Save to database
        result = supabase.table('Consultations').insert(consultation_data).execute()
        consultation_id = result.data[0]['id']
        print(f"✅ Created consultation: {consultation_id}")
        
        return jsonify({
            'success': True,
            'consultation_id': consultation_id,
            'priority': priority,
            'message': 'Consultation created. AI diagnosis will run after payment.'
        }), 201
    
    except Exception as e:
        print(f"❌ Error in botpress_webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/payment/create-link', methods=['POST'])
def create_payment_link():
    """
    Generate Paystack payment link for consultation
    """
    try:
        data = request.json
        consultation_id = data.get('consultation_id')
        consultation_type = data.get('consultation_type', 'doctor')
        patient_email = data.get('patient_email', 'patient@ogadoctor.com')
        
        # Get consultation details
        consultation = supabase.table('Consultations')\
            .select('*')\
            .eq('id', consultation_id)\
            .single()\
            .execute().data
        
        if not consultation:
            return jsonify({'error': 'Consultation not found'}), 404
        
        # Determine amount (in kobo - Paystack uses kobo)
        if consultation_type == 'pharmacist':
            amount = 1000 * 100  # ₦1,000 in kobo
        else:
            amount = 1500 * 100  # ₦1,500 in kobo
        
        # Create Paystack payment link
        paystack_url = 'https://api.paystack.co/transaction/initialize'
        
        headers = {
            'Authorization': f'Bearer {os.getenv("PAYSTACK_SECRET_KEY")}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'email': patient_email,
            'amount': amount,
            'metadata': {
                'consultation_id': consultation_id,
                'consultation_type': consultation_type,
                'patient_name': consultation['patient_name'],
                'patient_phone': consultation['patient_phone'],
                'symptoms': consultation['symptoms'],
                'severity': consultation['severity'],
                'duration': consultation['duration']
            },
            'callback_url': 'https://ogadoctor-analytics-dashboard.onrender.com/payment/callback'
        }
        
        response = requests.post(paystack_url, json=payload, headers=headers)
        result = response.json()
        
        if result['status']:
            payment_url = result['data']['authorization_url']
            reference = result['data']['reference']
            
            # Update consultation with payment reference
            supabase.table('Consultations').update({
                'payment_reference': reference,
                'payment_url': payment_url
            }).eq('id', consultation_id).execute()
            
            return jsonify({
                'success': True,
                'payment_url': payment_url,
                'reference': reference,
                'amount': amount / 100  # Convert back to naira
            }), 200
        else:
            return jsonify({'error': result.get('message', 'Payment link creation failed')}), 400
    
    except Exception as e:
        print(f"❌ Error creating payment link: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/payment/callback', methods=['GET'])
def payment_callback():
    """
    Handle Paystack payment callback (redirect after payment)
    """
    reference = request.args.get('reference')
    
    if reference:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Successful - OgaDoctor</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    max-width: 500px;
                }}
                .success-icon {{
                    font-size: 80px;
                    color: #4CAF50;
                }}
                h1 {{
                    color: #333;
                    margin: 20px 0;
                }}
                p {{
                    color: #666;
                    font-size: 18px;
                    line-height: 1.6;
                }}
                .reference {{
                    background: #f0f0f0;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Payment Successful!</h1>
                <p>Your consultation has been paid for. Our AI is analyzing your symptoms now.</p>
                <p>You will receive a WhatsApp message shortly with:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>AI diagnosis</li>
                    <li>Medication recommendations</li>
                    <li>Your assigned doctor/pharmacist details</li>
                </ul>
                <div class="reference">
                    <small>Reference: {reference}</small>
                </div>
                <p><strong>Thank you for using OgaDoctor! 🩺</strong></p>
            </div>
        </body>
        </html>
        """
    else:
        return "Payment verification pending...", 200

@app.route('/webhook/paystack', methods=['POST'])
def paystack_webhook():
    """
    Receive payment confirmation from Paystack
    Run AI diagnosis, then assign consultation to doctor or pharmacist
    """
    try:
        data = request.json
        print(f"💰 Received from Paystack: {data.get('event')}")
        
        if data.get('event') == 'charge.success':
            payment_data = data.get('data', {})
            
            reference = payment_data.get('reference')
            amount = payment_data.get('amount') / 100  # kobo to naira
            metadata = payment_data.get('metadata', {})
            
            consultation_id = metadata.get('consultation_id')
            consultation_type = metadata.get('consultation_type', 'doctor')
            symptoms = metadata.get('symptoms', '')
            severity = metadata.get('severity', '')
            duration = metadata.get('duration', '')
            
            if not consultation_id:
                return jsonify({'success': False, 'error': 'No consultation_id'}), 400
            
            # Update payment status
            supabase.table('Consultations').update({
                'payment_status': 'paid',
                'payment_reference': reference,
                'status': 'paid'
            }).eq('id', consultation_id).execute()
            print(f"✅ Updated payment status for: {consultation_id}")
            
            # RUN AI DIAGNOSIS NOW (after payment confirmed)
            print(f"🤖 Running AI diagnosis...")
            ai_diagnosis, ai_medications = run_ai_diagnosis(symptoms, severity, duration)
            
            # Update consultation with AI results
            supabase.table('Consultations').update({
                'ai_diagnosis': ai_diagnosis,
                'ai_drug_recommendations': ai_medications
            }).eq('id', consultation_id).execute()
            print(f"✅ AI diagnosis saved to consultation: {consultation_id}")
            
            # Get consultation with AI results
            consultation = supabase.table('Consultations')\
                .select('*')\
                .eq('id', consultation_id)\
                .single()\
                .execute().data
            
            # Assign to provider
            if consultation_type == 'doctor':
                provider_id, provider_phone = assign_to_available_doctor()
                if provider_id:
                    supabase.table('Consultations').update({
                        'doctor_id': provider_id,
                        'status': 'assigned',
                        'assigned_at': datetime.now().isoformat()
                    }).eq('id', consultation_id).execute()
                    print(f"✅ Assigned to doctor: {provider_id}")
                    
                    # Notify doctor
                    send_whatsapp_notification(
                        provider_phone,
                        f"🩺 New paid consultation!\n\nPatient: {consultation['patient_name']}\nSymptoms: {consultation['symptoms']}\nAI Diagnosis: {ai_diagnosis}\n\nLogin to start video call!"
                    )
                    
                    # Confirm to patient
                    send_whatsapp_notification(
                        consultation['patient_phone'],
                        f"✅ Payment confirmed! ₦{amount:,.0f}\n\n🤖 AI Diagnosis: {ai_diagnosis}\n\n💊 Recommended: {ai_medications}\n\nYour doctor will call you soon via video.\n\nThank you for using OgaDoctor! 🩺"
                    )
            
            elif consultation_type == 'pharmacist':
                provider_id, provider_phone = assign_to_available_pharmacist()
                if provider_id:
                    supabase.table('Consultations').update({
                        'pharmacist_id': provider_id,
                        'status': 'assigned',
                        'assigned_at': datetime.now().isoformat()
                    }).eq('id', consultation_id).execute()
                    print(f"✅ Assigned to pharmacist: {provider_id}")
                    
                    # Notify pharmacist
                    send_whatsapp_notification(
                        provider_phone,
                        f"💊 New paid consultation!\n\nPatient: {consultation['patient_name']}\nSymptoms: {consultation['symptoms']}\nAI Diagnosis: {ai_diagnosis}\n\nLogin to start video call!"
                    )
                    
                    # Confirm to patient
                    send_whatsapp_notification(
                        consultation['patient_phone'],
                        f"✅ Payment confirmed! ₦{amount:,.0f}\n\n🤖 AI Diagnosis: {ai_diagnosis}\n\n💊 Recommended: {ai_medications}\n\nYour pharmacist will call you soon via video.\n\nThank you for using OgaDoctor! 💊"
                    )
            
            return jsonify({'success': True}), 200
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"❌ Error in paystack webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/video/create-room', methods=['POST'])
def create_video_room():
    """
    Create Twilio video room for consultation
    Returns access tokens for patient and doctor/pharmacist
    """
    try:
        data = request.json
        consultation_id = data.get('consultation_id')
        role = data.get('role', 'patient')  # patient, doctor, or pharmacist
        
        if not consultation_id:
            return jsonify({'error': 'consultation_id required'}), 400
        
        # Get consultation details
        consultation = supabase.table('Consultations')\
            .select('*, doctors(*), pharmacists(*)')\
            .eq('id', consultation_id)\
            .single()\
            .execute().data
        
        # Create unique room name
        room_name = f"consultation_{consultation_id}"
        
        # Determine identity based on role
        if role == 'patient':
            identity = f"patient_{str(consultation_id)[:8]}"
        elif role == 'doctor':
            identity = f"doctor_{str(consultation.get('doctor_id', 'unknown'))[:8]}"
        elif role == 'pharmacist':
            identity = f"pharmacist_{str(consultation.get('pharmacist_id', 'unknown'))[:8]}"
        else:
            identity = f"user_{str(consultation_id)[:8]}"
        
        # Create access token
        token = AccessToken(
            TWILIO_ACCOUNT_SID,
            TWILIO_API_KEY,
            TWILIO_API_SECRET,
            identity=identity
        )
        
        # Add video grant
        token.add_grant(VideoGrant(room=room_name))
        
        # Generate JWT
        jwt_token = token.to_jwt()
        
        return jsonify({
            'success': True,
            'room_name': room_name,
            'token': jwt_token,
            'identity': identity,
            'expires_in': 3600  # 1 hour
        }), 200
    
    except Exception as e:
        print(f"❌ Error creating video room: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test', methods=['POST'])
def test_consultation():
    """Test endpoint - create a test consultation"""
    try:
        data = request.json or {}
        
        result = supabase.table('Consultations').insert({
            'patient_name': data.get('patient_name', 'Test Patient'),
            'patient_phone': data.get('patient_phone', '+234803TESTPAT'),
            'symptoms': data.get('symptoms', 'Test headache and fever'),
            'severity': 'moderate',
            'duration': '2 days',
            'priority': 'MODERATE',
            'status': 'pending',
            'payment_status': 'unpaid',
            'consultation_fee': 1500,
            'provider_payout': 1000,
            'platform_commission': 500,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return jsonify({
            'success': True,
            'consultation': result.data[0],
            'message': 'Test consultation created! Check your admin dashboard.'
        }), 201
    
    except Exception as e:
        print(f"❌ Error creating test: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"""
    🚀 OgaDoctor Backend Server - Video System with AI
    ==================================================
    
    📍 Port: {port}
    🔗 Endpoints:
       - GET  /                       (health check)
       - POST /webhook/botpress       (receive consultations - no AI yet)
       - POST /webhook/paystack       (payment + AI diagnosis + assignment)
       - POST /payment/create-link    (generate payment link)
       - GET  /payment/callback       (payment success page)
       - POST /video/create-room      (create video call)
       - POST /api/test               (test consultation)
    
    🎥 Twilio Video: {'✅ Connected' if TWILIO_ACCOUNT_SID else '❌ Not configured'}
    💾 Supabase: {'✅ Connected' if SUPABASE_URL else '❌ Not configured'}
    💰 Paystack: {'✅ Connected' if os.getenv("PAYSTACK_SECRET_KEY") else '❌ Not configured'}
    🤖 OpenAI: {'✅ Connected' if OPENAI_API_KEY else '❌ Not configured'}
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
