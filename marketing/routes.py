from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from .models import Contact, Campaign, CampaignMetrics
from extensions import db
from datetime import datetime
from mailjet_rest import Client
import os

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

# Aquí puedes agregar más rutas API para manejar plantillas, reportes, segmentación, etc.