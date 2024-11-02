from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user
from .models import Contact, Campaign, CampaignMetrics, CampaignImage
from extensions import db
from datetime import datetime
from mailjet_rest import Client
import os
import requests
import base64
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

marketing = Blueprint('marketing', __name__)

mailjet = Client(auth=(os.getenv('MJ_APIKEY_PUBLIC'), os.getenv('MJ_APIKEY_PRIVATE')), version='v3.1')

@marketing.route('/')
@login_required
def index():
    return render_template('marketing/index.html')

@marketing.route('/contacts')
@login_required
def contacts():
    return render_template('marketing/contacts.html')

@marketing.route('/campaigns')
@login_required
def campaigns():
    return render_template('marketing/campaigns.html')

@marketing.route('/templates')
@login_required
def templates():
    return render_template('marketing/templates.html')

@marketing.route('/reports')
@login_required
def reports():
    return render_template('marketing/reports.html')

@marketing.route('/segmentation')
@login_required
def segmentation():
    return render_template('marketing/segmentation.html')

@marketing.route('/automation')
@marketing.route('/automations')
@login_required
def automation():
    return render_template('marketing/automation.html')

@marketing.route('/social_media')
@marketing.route('/social-media')
@login_required
def social_media():
    return render_template('marketing/social_media.html')

@marketing.route('/api/contacts', methods=['GET', 'POST'])
@login_required
def manage_contacts():
    if request.method == 'GET':
        contacts = Contact.query.filter_by(user_id=current_user.id).all()
        return jsonify([c.to_dict() for c in contacts])
    elif request.method == 'POST':
        data = request.json
        try:
            new_contact = Contact(
                name=data['name'],
                email=data['email'],
                company=data.get('company'),
                user_id=current_user.id
            )
            db.session.add(new_contact)
            db.session.commit()
            return jsonify({'message': 'Contact added successfully', 'contact': new_contact.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

@marketing.route('/api/campaigns', methods=['GET', 'POST'])
@login_required
def manage_campaigns():
    if request.method == 'GET':
        campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': c.id,
            'name': c.name,
            'subject': c.subject,
            'sent_at': c.sent_at
        } for c in campaigns])
    elif request.method == 'POST':
        data = request.json
        new_campaign = Campaign(
            name=data['name'],
            subject=data['subject'],
            content=data['content'],
            user_id=current_user.id
        )
        db.session.add(new_campaign)
        db.session.commit()
        return jsonify({'message': 'Campaign created successfully'}), 201

@marketing.route('/api/send_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    contacts = Contact.query.filter_by(user_id=current_user.id, subscribed=True).all()
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "your-email@example.com",
                    "Name": "Your Name"
                },
                "To": [{"Email": contact.email, "Name": contact.name} for contact in contacts],
                "Subject": campaign.subject,
                "HTMLPart": campaign.content
            }
        ]
    }
    
    try:
        result = mailjet.send.create(data=data)
        if result.status_code == 200:
            campaign.sent_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Campaign sent successfully'}), 200
        else:
            return jsonify({'error': 'Failed to send campaign', 'details': result.json()}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred while sending the campaign'}), 500

@marketing.route('/api/campaign_metrics/<int:campaign_id>', methods=['GET'])
@login_required
def get_campaign_metrics(campaign_id):
    metrics = CampaignMetrics.query.filter_by(campaign_id=campaign_id).first()
    if metrics:
        return jsonify({
            'opens': metrics.opens,
            'clicks': metrics.clicks,
            'bounces': metrics.bounces,
            'unsubscribes': metrics.unsubscribes
        })
    else:
        return jsonify({'error': 'Metrics not found'}), 404

@marketing.route('/api/submodulos/Marketing')
@login_required
def get_marketing_submodulos():
    submodulos = [
        "Gestión de Contactos",
        "Campañas de Email",
        "Plantillas de Email",
        "Reportes de Campañas",
        "Segmentación de Contactos",
        "Automatizaciones",
        "Integración de Redes Sociales"
    ]
    return jsonify(submodulos)

@marketing.route('/api/generate-image', methods=['POST'])
@login_required
def generate_image():
    try:
        data = request.json
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        # Hugging Face API endpoint for Stable Diffusion 3.5
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
        headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}",
            "Content-Type": "application/json"
        }

        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            # Make request to Hugging Face API
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt}
            )

            if response.status_code == 200:
                # The response will be the binary image data
                # We'll send it back as base64 so it can be displayed in the frontend
                image_bytes = response.content
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

                return jsonify({
                    'success': True,
                    'image': f'data:image/jpeg;base64,{base64_image}'
                })
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    current_app.logger.error("Max retries reached for rate limit error")
                    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            else:
                current_app.logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                return jsonify({
                    'error': 'Error generating image',
                    'details': response.text
                }), response.status_code

    except requests.RequestException as e:
        current_app.logger.error(f"Network error when calling Hugging Face API: {str(e)}")
        return jsonify({'error': 'Network error occurred. Please try again.'}), 503

    except Exception as e:
        current_app.logger.error(f"Unexpected error generating image: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@marketing.route('/api/save-generated-image', methods=['POST'])
@login_required
def save_generated_image():
    try:
        data = request.json
        image_data = data.get('image')
        campaign_id = data.get('campaign_id')
        
        if not image_data or not campaign_id:
            return jsonify({'error': 'Missing required data'}), 400

        # Remove the data URL prefix to get just the base64 data
        base64_data = image_data.replace('data:image/jpeg;base64,', '')
        
        # Create a directory for campaign images if it doesn't exist
        campaign_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], f'campaign_{campaign_id}')
        os.makedirs(campaign_dir, exist_ok=True)
        
        # Generate a unique filename
        filename = f'generated_image_{int(time.time())}.jpg'
        filepath = os.path.join(campaign_dir, filename)
        
        # Save the image
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(base64_data))
        
        # Save the image reference in your database
        image = CampaignImage(
            campaign_id=campaign_id,
            filepath=filepath,
            created_by=current_user.id
        )
        db.session.add(image)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filepath': filepath
        })

    except Exception as e:
        current_app.logger.error(f"Error saving generated image: {str(e)}")
        return jsonify({'error': str(e)}), 500