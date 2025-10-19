# --- modules/legal_pi/stripe_handler.py ---
import os
import stripe
from datetime import datetime
from database import get_supabase_client

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def log(message):
    print(f"[{datetime.utcnow().isoformat()}] {message}")

def create_payment_link_for_lead(lead_data, lawyer_data):
    """
    Creates a Stripe payment link for a lawyer to buy a lead.
    
    Args:
        lead_data: Injured person info
        lawyer_data: PI lawyer info
    
    Returns:
        str: Payment link URL
    """
    try:
        # Create Stripe product (one-time)
        product = stripe.Product.create(
            name=f"PI Lead: {lead_data['injury_type']} - {lead_data['city']}",
            description=f"Quality Score: {lead_data['quality_score']}/10\n{lead_data['description'][:100]}",
        )
        
        # Create price (pay-per-lead: $800)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=80000,  # $800 in cents
            currency='usd',
        )
        
        # Create payment link
        payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    'price': price.id,
                    'quantity': 1,
                }
            ],
            metadata={
                'lead_id': lead_data['id'],
                'lawyer_id': lawyer_data['id'],
                'injury_type': lead_data['injury_type'],
                'city': lead_data['city']
            },
            after_completion={
                'type': 'hosted_confirmation',
                'hosted_confirmation': {
                    'custom_message': "Payment successful! We'll send the lead details to your email within 5 minutes."
                }
            }
        )
        
        log(f"✅ Created payment link: {payment_link.url}")
        return payment_link.url
    
    except Exception as e:
        log(f"❌ Stripe error: {e}")
        return None

def create_subscription_for_lawyer(lawyer_data, plan='monthly'):
    """
    Creates monthly subscription ($3,000/month for 10-15 leads).
    
    Args:
        lawyer_data: PI lawyer info
        plan: 'monthly' or 'annual'
    
    Returns:
        str: Checkout session URL
    """
    try:
        # Create or get existing customer
        customer = stripe.Customer.create(
            email=lawyer_data['contact_email'],
            name=lawyer_data['business_name'],
            metadata={
                'lawyer_id': lawyer_data['id'],
                'city': lawyer_data['city']
            }
        )
        
        # Create subscription checkout
        price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')  # Set this in .env
        
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://yourdomain.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://yourdomain.com/cancel',
            metadata={
                'lawyer_id': lawyer_data['id'],
                'plan': plan
            }
        )
        
        log(f"✅ Created subscription checkout: {checkout_session.url}")
        return checkout_session.url
    
    except Exception as e:
        log(f"❌ Stripe error: {e}")
        return None

def handle_successful_payment(session_id):
    """
    Processes successful payment and delivers lead.
    Called by webhook.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            metadata = session.metadata
            lead_id = metadata.get('lead_id')
            lawyer_id = metadata.get('lawyer_id')
            
            # Update database
            supabase = get_supabase_client()
            
            # Mark lead as sold
            supabase.table('injured_people_leads').update({
                'status': 'sold',
                'sold_to_lawyer_id': lawyer_id,
                'sold_at': datetime.utcnow().isoformat(),
                'sale_price': 800.00
            }).eq('id', lead_id).execute()
            
            # Create delivery record
            supabase.table('lead_deliveries').insert({
                'lead_id': lead_id,
                'lawyer_id': lawyer_id,
                'payment_status': 'paid',
                'payment_amount': 800.00,
                'stripe_session_id': session_id,
                'delivered_at': datetime.utcnow().isoformat()
            }).execute()
            
            log(f"✅ Lead {lead_id} sold to lawyer {lawyer_id}")
            
            # TODO: Send lead details to lawyer via email
            return True
    
    except Exception as e:
        log(f"❌ Error processing payment: {e}")
        return False
