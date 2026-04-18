const express = require('express');
const PDFDocument = require('pdfkit');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.post('/generate-pdf', (req, res) => {
  try {
    const data = req.body;
    
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=invoice_${data.invoiceNumber}.pdf`);
    
    const doc = new PDFDocument({ margin: 50, size: 'A4' });
    doc.pipe(res);
    
    // Header
    doc.fontSize(24).font('Helvetica-Bold').text('Roburwoods Furniture', { align: 'center' });
    doc.moveDown();
    doc.fontSize(18).text('TAX INVOICE', { align: 'center' });
    doc.fontSize(12).font('Helvetica').text(`#${data.formattedNumber}`, { align: 'center' });
    doc.moveDown();
    
    // Customer info
    doc.fontSize(10);
    doc.text(`Customer: ${data.customer.name}`);
    doc.text(`Email: ${data.customer.email}`);
    doc.text(`Phone: ${data.customer.phone || 'N/A'}`);
    doc.text(`Date: ${data.date}`);
    doc.text(`Due Date: ${data.dueDate}`);
    doc.moveDown();
    
    // Items table header
    let y = doc.y;
    doc.font('Helvetica-Bold');
    doc.text('Item', 50, y);
    doc.text('Qty', 250, y);
    doc.text('Price', 350, y);
    doc.text('Total', 450, y);
    
    doc.font('Helvetica');
    y += 20;
    
    // Items
    for (const item of data.items) {
      if (item.name) {
        const qty = Number(item.quantity) || 0;
        const price = Number(item.unit_price) || 0;
        const itemTotal = qty * price;
        doc.text(item.name, 50, y);
        doc.text(qty.toString(), 250, y);
        doc.text(`$${price.toFixed(2)}`, 350, y);
        doc.text(`$${itemTotal.toFixed(2)}`, 450, y);
        y += 20;
        
        if (y > 700) {
          doc.addPage();
          y = 50;
        }
      }
    }
    
    // Totals
    y += 20;
    doc.font('Helvetica');
    doc.text(`Subtotal: $${data.subtotal.toFixed(2)}`, 350, y);
    y += 15;
    doc.text(`VAT (15%): $${data.tax.toFixed(2)}`, 350, y);
    y += 15;
    doc.font('Helvetica-Bold');
    doc.text(`Total: $${data.total.toFixed(2)} USD`, 350, y);
    y += 30;
    
    // Footer
    doc.fontSize(9).font('Helvetica');
    doc.text('Roburwoods Furniture - 136 Elmswood Park, Marondera, Zimbabwe', 50, 750, { align: 'center' });
    doc.text('Tel: +263 772761564 | Email: info@roburwoods.com', 50, 765, { align: 'center' });
    
    doc.end();
    
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'PDF generation failed' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'Roburwoods PDF Service' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`PDF service running on port ${PORT}`));