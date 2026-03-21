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

app = Flask(__name__)

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

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

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

def send_whatsapp_notification(phone_number, message):
    """Send WhatsApp notification (placeholder for now)"""
    print(f"📱 WhatsApp to {phone_number}: {message}")
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
        'version': '2.0',
        'features': [
            'Encrypted video consultations',
            'Botpress integration',
            'Paystack payments',
            'Doctor and Pharmacist assignment'
        ]
    })

@app.route('/webhook/botpress', methods=['POST'])
def botpress_webhook():
    """
    Receive patient consultation data from Botpress
    
    Expected JSON:
    {
        "patient_name": "Amaka Obi",
        "patient_phone": "+234803XXXXXXX",
        "symptoms": "Headache and fever",
        "severity": "Strong",
        "duration": "2 days",
        "consultation_type": "doctor",
        "ai_diagnosis": "...",
        "ai_drug_recommendations": "...",
        "payment_reference": "PAY_xxx" (optional)
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
        ai_diagnosis = data.get('ai_diagnosis', '')
        ai_drug_recommendations = data.get('ai_drug_recommendations', '')
        payment_reference = data.get('payment_reference', '')
        
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
        
        # Create consultation
        consultation_data = {
            'patient_name': patient_name,
            'patient_phone': patient_phone,
            'user_id': user_id,
            'symptoms': symptoms,
            'severity': severity,
            'duration': duration,
            'priority': priority,
            'status': 'pending' if not payment_reference else 'paid',
            'payment_status': 'paid' if payment_reference else 'unpaid',
            'payment_reference': payment_reference,
            'consultation_fee': consultation_fee,
            'ai_diagnosis': ai_diagnosis,
            'ai_drug_recommendations': ai_drug_recommendations,
            'platform_commission': platform_commission,
            'provider_payout': provider_payout,
            'created_at': datetime.now().isoformat()
        }
        
        # Save to database
        result = supabase.table('Consultations').insert(consultation_data).execute()
        consultation_id = result.data[0]['id']
        print(f"✅ Created consultation: {consultation_id}")
        
        # If already paid, assign to provider
        if payment_reference:
            if consultation_type == 'doctor':
                provider_id, provider_phone = assign_to_available_doctor()
                if provider_id:
                    supabase.table('Consultations').update({
                        'doctor_id': provider_id,
                        'status': 'assigned',
                        'assigned_at': datetime.now().isoformat()
                    }).eq('id', consultation_id).execute()
                    print(f"✅ Assigned to doctor: {provider_id}")
                    
                    send_whatsapp_notification(
                        provider_phone,
                        f"🩺 New consultation assigned!\n\nPatient: {patient_name}\nSymptoms: {symptoms}\n\nLogin to start video call!"
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
                    
                    send_whatsapp_notification(
                        provider_phone,
                        f"💊 New consultation assigned!\n\nPatient: {patient_name}\nSymptoms: {symptoms}\n\nLogin to start video call!"
                    )
        
        return jsonify({
            'success': True,
            'consultation_id': consultation_id,
            'priority': priority,
            'message': 'Consultation created successfully'
        }), 201
    
    except Exception as e:
        print(f"❌ Error in botpress_webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/webhook/paystack', methods=['POST'])
def paystack_webhook():
    """
    Receive payment confirmation from Paystack
    Assign consultation to doctor or pharmacist
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
            
            if not consultation_id:
                return jsonify({'success': False, 'error': 'No consultation_id'}), 400
            
            # Update payment status
            supabase.table('Consultations').update({
                'payment_status': 'paid',
                'payment_reference': reference,
                'status': 'paid'
            }).eq('id', consultation_id).execute()
            print(f"✅ Updated payment status for: {consultation_id}")
            
            # Get consultation
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
                        f"🩺 New paid consultation!\n\nPatient: {consultation['patient_name']}\nSymptoms: {consultation['symptoms']}\n\nLogin to start video call!"
                    )
                    
                    # Confirm to patient
                    send_whatsapp_notification(
                        consultation['patient_phone'],
                        f"✅ Payment confirmed! ₦{amount:,.0f}\n\nYour doctor will call you soon via video.\n\nThank you for using OgaDoctor! 🩺"
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
                        f"💊 New paid consultation!\n\nPatient: {consultation['patient_name']}\nSymptoms: {consultation['symptoms']}\n\nLogin to start video call!"
                    )
                    
                    # Confirm to patient
                    send_whatsapp_notification(
                        consultation['patient_phone'],
                        f"✅ Payment confirmed! ₦{amount:,.0f}\n\nYour pharmacist will call you soon via video.\n\nThank you for using OgaDoctor! 💊"
                    )
            
            return jsonify({'success': True}), 200
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"❌ Error in paystack webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
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
                'patient_phone': consultation['patient_phone']
            },
            'callback_url': 'https://ogadoctor-analytics-dashboard.onrender.com/payment/callback'
        }
        
        import requests
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
    🚀 OgaDoctor Backend Server - Video System
    ==========================================
    
    📍 Port: {port}
    🔗 Endpoints:
       - GET  /                       (health check)
       - POST /webhook/botpress       (receive consultations)
       - POST /webhook/paystack       (payment confirmation)
       - POST /video/create-room      (create video call)
       - POST /api/test               (test consultation)
    
    🎥 Twilio Video: {'✅ Connected' if TWILIO_ACCOUNT_SID else '❌ Not configured'}
    💾 Supabase: {'✅ Connected' if SUPABASE_URL else '❌ Not configured'}
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
