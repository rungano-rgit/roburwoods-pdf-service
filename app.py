from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from weasyprint import HTML
import uuid
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow requests from your Vercel app

# Create folder for generated PDFs
PDF_FOLDER = 'generated_pdfs'
os.makedirs(PDF_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Roburwoods PDF Generator',
        'status': 'running',
        'endpoints': {
            'POST /generate-pdf': 'Generate PDF from invoice data',
            'GET /pdfs/<filename>': 'Download generated PDF'
        }
    })

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        print(f"Received request for: {data.get('customer', {}).get('name', 'Unknown')}")
        
        # Generate unique ID
        pdf_id = str(uuid.uuid4())[:8]
        filename = f"invoice_{pdf_id}.pdf"
        filepath = os.path.join(PDF_FOLDER, filename)
        
        # Generate HTML from received data
        html_content = generate_invoice_html(data)
        
        # Create PDF
        HTML(string=html_content).write_pdf(filepath)
        
        # Generate URLs
        pdf_url = f"https://{request.host}/pdfs/{filename}"
        
        # Get customer phone for WhatsApp
        customer_phone = data.get('customer', {}).get('phone', '')
        # Remove any non-digit characters
        customer_phone = ''.join(filter(str.isdigit, customer_phone))
        
        # Prepare WhatsApp link
        message = f"Your invoice is ready! 📄\\n\\nDownload: {pdf_url}\\n\\nThank you for choosing Roburwoods Furniture!"
        whatsapp_link = f"https://wa.me/{customer_phone}?text={message}" if customer_phone else None
        
        return jsonify({
            'success': True,
            'pdf_url': pdf_url,
            'whatsapp_link': whatsapp_link,
            'pdf_id': pdf_id,
            'message': 'PDF generated successfully'
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/pdfs/<filename>', methods=['GET'])
def download_pdf(filename):
    filepath = os.path.join(PDF_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=False, mimetype='application/pdf')
    return jsonify({'error': 'File not found'}), 404

def generate_invoice_html(data):
    customer = data.get('customer', {})
    items = data.get('items', [])
    subtotal = data.get('subtotal', 0)
    tax = data.get('tax', 0)
    total = data.get('total', 0)
    invoice_number = data.get('invoice_number', f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    notes = data.get('notes', '')
    
    items_html = ""
    for item in items:
        qty = item.get('quantity', 0)
        price = item.get('unit_price', 0)
        item_total = qty * price
        items_html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{item.get('name', 'Item')}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{qty}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${price:.2f}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${item_total:.2f}</td>
         </tr>
        """
    
    if not items_html:
        items_html = '<tr><td colspan="4" style="text-align: center;">No items</td></tr>'
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Invoice - Roburwoods Furniture</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; margin: 0; background: #f5f5f5; }}
            .invoice-container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #1a472a 0%, #2d5a3b 100%); padding: 30px; color: white; text-align: center; }}
            .company-name {{ font-size: 28px; font-weight: bold; margin-bottom: 5px; }}
            .title {{ font-size: 24px; margin: 20px 0; font-weight: bold; }}
            .invoice-number {{ font-size: 14px; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .info-section {{ display: flex; justify-content: space-between; margin-bottom: 30px; background: #f5f5f5; padding: 15px; border-radius: 8px; }}
            .info-box {{ flex: 1; }}
            .info-label {{ font-weight: bold; color: #2d5a3b; margin-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background: #2d5a3b; color: white; padding: 12px; text-align: left; }}
            td {{ border-bottom: 1px solid #ddd; padding: 10px; }}
            .totals {{ text-align: right; margin-top: 20px; padding-top: 20px; border-top: 2px solid #2d5a3b; }}
            .grand-total {{ font-size: 18px; font-weight: bold; color: #2d5a3b; margin-top: 10px; }}
            .footer {{ background: #f5f5f5; padding: 20px; text-align: center; font-size: 11px; color: #666; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="invoice-container">
            <div class="header">
                <div class="company-name">Roburwoods Furniture</div>
                <div class="title">TAX INVOICE</div>
                <div class="invoice-number">#{invoice_number}</div>
            </div>
            <div class="content">
                <div class="info-section">
                    <div class="info-box">
                        <div class="info-label">BILL TO</div>
                        <p><strong>{customer.get('name', 'N/A')}</strong></p>
                        <p>{customer.get('email', 'N/A')}</p>
                        <p>{customer.get('phone', 'N/A')}</p>
                        <p>{customer.get('address', 'N/A')}</p>
                    </div>
                    <div class="info-box">
                        <div class="info-label">INVOICE DETAILS</div>
                        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                        <p><strong>Currency:</strong> USD</p>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th style="text-align: center">Qty</th>
                            <th style="text-align: right">Unit Price</th>
                            <th style="text-align: right">Total</th>
                         </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
                
                <div class="totals">
                    <div>Subtotal: ${subtotal:.2f}</div>
                    <div>VAT (15%): ${tax:.2f}</div>
                    <div class="grand-total">TOTAL: ${total:.2f} USD</div>
                </div>
                
                {f'<div style="margin-top: 20px; padding: 10px; background: #e8f5e9; border-radius: 8px;"><strong>📝 Notes:</strong><br>{notes}</div>' if notes else ''}
                
                <div style="margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 8px;">
                    <strong>💰 Payment Information:</strong><br>
                    • Bank Transfer: CBZ Bank, Account: 09026193970026<br>
                    • EcoCash: Merchant Code 046756
                </div>
            </div>
            <div class="footer">
                <p>Roburwoods Furniture - 136 Elmswood Park, Marondera, Zimbabwe</p>
                <p>Tel: +263 772761564 | Email: info@roburwoods.com</p>
                <p>Thank you for choosing Roburwoods Furniture</p>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)