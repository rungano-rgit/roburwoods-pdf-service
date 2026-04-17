from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import os
from datetime import datetime
import io

# Use reportlab instead of weasyprint (more reliable on Render)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

app = Flask(__name__)
CORS(app)

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
        
        # Generate PDF using reportlab
        generate_pdf_reportlab(filepath, data)
        
        # Generate URLs
        pdf_url = f"https://{request.host}/pdfs/{filename}"
        
        # Get customer phone for WhatsApp
        customer_phone = data.get('customer', {}).get('phone', '')
        customer_phone = ''.join(filter(str.isdigit, customer_phone))
        
        # Prepare WhatsApp link
        message = f"Your invoice is ready! 📄\n\nDownload: {pdf_url}\n\nThank you for choosing Roburwoods Furniture!"
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

def generate_pdf_reportlab(filepath, data):
    """Generate PDF using reportlab"""
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a472a'),
        alignment=1,  # Center
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2d5a3b'),
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("Roburwoods Furniture", title_style))
    story.append(Paragraph("TAX INVOICE", heading_style))
    story.append(Spacer(1, 20))
    
    # Customer info
    customer = data.get('customer', {})
    story.append(Paragraph(f"<b>Customer:</b> {customer.get('name', 'N/A')}", normal_style))
    story.append(Paragraph(f"<b>Email:</b> {customer.get('email', 'N/A')}", normal_style))
    story.append(Paragraph(f"<b>Phone:</b> {customer.get('phone', 'N/A')}", normal_style))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Items table
    items = data.get('items', [])
    table_data = [['Item', 'Qty', 'Unit Price', 'Total']]
    
    for item in items:
        qty = item.get('quantity', 0)
        price = item.get('unit_price', 0)
        total = qty * price
        table_data.append([
            item.get('name', 'Item'),
            str(qty),
            f"${price:.2f}",
            f"${total:.2f}"
        ])
    
    # Add totals row
    subtotal = data.get('subtotal', 0)
    tax = data.get('tax', 0)
    total = data.get('total', 0)
    table_data.append(['', '', '<b>Subtotal:</b>', f"<b>${subtotal:.2f}</b>"])
    table_data.append(['', '', '<b>VAT (15%):</b>', f"<b>${tax:.2f}</b>"])
    table_data.append(['', '', '<b>TOTAL:</b>', f"<b>${total:.2f} USD</b>"])
    
    # Create table
    table = Table(table_data, colWidths=[2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5a3b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('GRID', (0, 0), (-1, -4), 1, colors.grey),
        ('SPAN', (0, -3), (1, -3)),  # Span for Subtotal label
        ('SPAN', (0, -2), (1, -2)),  # Span for VAT label
        ('SPAN', (0, -1), (1, -1)),  # Span for TOTAL label
        ('ALIGN', (2, -3), (-1, -1), 'RIGHT'),
        ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Notes
    notes = data.get('notes', '')
    if notes:
        story.append(Paragraph(f"<b>Notes:</b> {notes}", normal_style))
        story.append(Spacer(1, 10))
    
    # Footer
    footer_text = """
    <b>Payment Information:</b><br/>
    • Bank Transfer: CBZ Bank, Account: 09026193970026<br/>
    • EcoCash: Merchant Code 046756<br/>
    <br/>
    Roburwoods Furniture - 136 Elmswood Park, Marondera, Zimbabwe<br/>
    Tel: +263 772761564 | Email: info@roburwoods.com
    """
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)