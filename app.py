from flask import Flask, request, jsonify
import win32printing
import win32api
import win32print
import datetime
import jinja2
import pdfkit
import os

os.add_dll_directory(r"C:\Program Files\GTK3-Runtime Win64\bin")
from weasyprint import HTML, CSS
version = '1.0.0'
app = Flask(__name__)
environment = jinja2.Environment()
billTemplate = '''
<div id="bill">
    <h3 style="text-align: center;font-style:bold;">{{projectName}}</h3>
    <h4 style="text-align: center" {% if address%}">
        {{dataProvider.currentProject.address}}</h4>
        {% if phoneNumber %}
    <h4 style="text-align: center">Phone:
        {{dataProvider.currentProject.phoneNumber}}</h4>
        {% endif %}
    <hr>
    {% if gstNo %}
    <div class="topFields">GST No.
        {{dataProvider.currentProject.gstNo}}</div>
        {% endif %}
    {% if fssaiNo %}
    <div class="topFields">FSSAI No.
        {{dataProvider.currentProject.fssaiNo}}</div>
        {% endif %}
    {% if counterNo %}
    <div class="topFields">Counter No.
        {{dataProvider.currentProject.counterNo}}</div>
        {% endif %}
    {% if cashierName %}
    <div class="topFields">Cashier.
        {{dataProvider.currentProject.cashierName}}</div>
        {% endif %}
    {% if deviceName %}
    <div class="topFields">Device Name.
        {{dataProvider.currentProject.deviceName}}</div>
    {% endif %}
    <div class="topFields">{{today | date:'medium'}}</div>
    <div class="topFields">Bill Id: {{currentBill.id}}</div>
    {% if customerInfoForm.value.fullName %}
    <h4 style="text-align: start">Name:
        {{customerInfoForm.value.fullName}}</h4>
    {% endif %}
    {% if customerInfoForm.value.phoneNumber %}
    <h4 style="text-align: start">Phone:
        {{customerInfoForm.value.phoneNumber}}</h4>
    {% endif %}
    <div class="row">
        <h4><b>Token No.:</b> {{currentBill.tokenNo}}</h4>
        {% if currentTable.type=='table' %}
            <h4><b>Table No.:</b> {{currentTable.tableNo}}</h4>
        {% endif %}
        {% if currentTable.type=='room' %}
            <h4><b>Room No.:</b> {{currentTable.tableNo}}</h4>
        {% endif %}
    </div>
    {% if isNonChargeable %}    
        <h3>Non Chargeable</h3>
    {% endif %}
    <table>
        <tr>
            <th>Product</th>
            <th>Qty</th>
            <th>Rate</th>
            <th>Amt</th>
        </tr>
        {% for product in allProducts %}
            <tr>
                <td>{{product.dishName}}</td>
                <td>{{product.quantity}}</td>
                <td>&#8377;{{product.shopPrice}}</td>
                <td>&#8377;{{toFixedValue(product.shopPrice * product.quantity)}}</td>
            </tr>
        {% endfor %}
    </table>
    {% if selectDiscounts.length > 0 %}
        <hr>
        <table>
            <h3>Discounts</h3>
            <tr>
                <th>Name</th>
                <th>Amount</th>
                <th>Type</th>
                <th>Final</th>
            </tr>
            <tr *ngFor="let item of selectDiscounts;let i = index;">
                <td>{{item.title}}</td>
                <td>{{item.discountValue}}</td>
                <td>{{item.discountType}}</td>
                <td>{{discountValues[i]}}</td>
            </tr>
        </table>
    {% endif %}
    <hr>
    {% if specialInstructions %}
        <p class="info">Special Instructions: {{specialInstructions}}</p>
        <hr>
    {% endif %}
    <div class="info">
        <p>Total Qty: {{totalQuantity}}</p>
        <p>Sub Total: &#8377;{{taxableValue}}</p>
    </div>
    <p class="detail">*Net Total Inclusive of GST</p>
    <hr>
    <div class="tax">
        <p>CGST</p>
        <p>%2.5</p>
        <p>&#8377;{{cgst}}</p>
    </div>
    <div class="tax">
        <p>SGST</p>
        <p>%2.5</p>
        <p>&#8377;{{sgst}}</p>
    </div>
    <hr>
    <div class="total">
        <p>Taxable Amount</p>
        <p>&#8377;{{taxableValue}}</p>
    </div>
    <div class="total"> 
        <p>Total Tax</p>
        <p>&#8377;{{totalTaxAmount}}</p>
    </div>
    <div class="total">
        <p>Grand Total</p>
        <p>&#8377;{{grandTotal}}</p>
    </div>
    <hr>
    <p class="thanking">Thanks for visiting {{ projectName }}</p>
    <p class="thanking">{{ website }}</p>
</div>
'''

kotTemplate = '''
<div id="billKot">
    <h3 style="text-align: center">{{data['hotelName']}}</h3>
    <h4 style="text-align: center">{{data['today']}}</h4>
    <h4 style="text-align: center">Bill Id: {{data['billId']}}</h4>
    {% if data['deskKot'] %} <h3>Order</h3> {% endif %}
    {% if not data['deskKot'] %} <h3>KOT</h3> {% endif %}
    {% if isNonChargeable %}
        <h3>Non Chargeable</h3>
    {% endif %}
    <div class="row">
        <h4><b>Token No.:</b> {{data['tokenNo']}}</h4>
        {% if data['tableType']=='table' %}
            <h4><b>Table No.:</b> {{data['tableNo']}}</h4>
        {% endif %}
        {% if data['tableType']=='room' %}
            <h4><b>Room No.:</b> {{data['tableNo']}}</h4>
        {% endif %}
    </div>
    <table>
        <tr>
            <th>Product</th>
            <th>Qty</th>
        </tr>
        {% for product in data['allProducts'] %}
            <tr>
                <td>{{product['dishName']}}</td>
                <td>{{product['quantity']}}</td>
            </tr>
        {% endfor %}
    </table>
    <hr>
    {% if specialInstructions %}
        <p class="info">Special Instructions: {{data['specialInstructions']}}</p>
    {% endif %}
</div>
'''

htmlBody = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bill</title>
    <link rel="stylesheet" href="style.css" />
</head>
<body>
{kotTemplate}
</body>
'''

kotInstance = environment.from_string(htmlBody)
data = {
    'hotelName': 'Hotel Name',
    'today': datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
    'billId': '97592839832',
    'deskKot': True,
    'tokenNo': 'Token No',
    'tableNo': '2',
    'tableType': 'table',
    'allProducts': [
        {
            'dishName': 'Dish Name',
            'quantity': '2'
        }
    ],
    'specialInstructions': 'Special Instructions'
}
# compiledKot= kotInstance.render(
#     data=data
# )
# with open('temp_kot.html', 'w') as f:
#     f.write(compiledKot)
# date = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
# print(f'kots/temp_kot_{date}.pdf')
# filename = f'kots/kot_{date}.pdf'
# HTML(string=compiledKot).write_pdf(filename,
#     stylesheets=[CSS(filename='style.css')])
# printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1)
# tempprinter = printers[0][2]
# print(tempprinter,"filename",filename)
# currentprinter = win32print.GetDefaultPrinter()
# win32print.SetDefaultPrinter(tempprinter)
# win32api.ShellExecute(0, 'open', 'gsprint.exe', '-printer '+tempprinter+' ' + filename, '.', 0)
# win32print.SetDefaultPrinter(currentprinter)

@app.route('/')
def checkServertatus():
    return f'Hello from Viraj servers. This is ' + version


@app.route('/getPrinters')
def getPrinters():
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1)
    printersList = []
    for printer in printers:
        print(printer)
        # for printerName in printer[2].split(','):
        printersList.append(printer[2])
    return {
        "message": "Found Printers",
        "code": True,
        "printers": printersList
    }


@app.route('/printKot', methods=['POST'])
def printKot():
    date = datetime.datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
    data = request.json
    # check for hotelName, hotelAddress, gstNo, fssaiNo, counterNo, billId, tokenNo, tableNo, specialInstructions, totalQty, taxes, taxableAmount, totalTax

    if ((not data['hotelName']) or data['hotelName'] == ''):
        return {"message": "Hotel Name is required", "code": False}
    if ((not data['hotelAddress']) or data['hotelAddress'] == ''):
        return {"message": "Hotel Address is required", "code": False}
    if ((not data['gstNo']) or data['gstNo'] == ''):
        return {"message": "GST No is required", "code": False}
    if ((not data['fssaiNo']) or data['fssaiNo'] == ''):
        return {"message": "FSSAI No is required", "code": False}
    if ((not data['counterNo']) or data['counterNo'] == ''):
        return {"message": "Counter No is required", "code": False}
    if ((not data['billId']) or data['billId'] == ''):
        return {"message": "Bill Id is required", "code": False}
    if ((not data['tokenNo']) or data['tokenNo'] == ''):
        return {"message": "Token No is required", "code": False}
    if ((not data['tableNo']) or data['tableNo'] == ''):
        return {"message": "Table No is required", "code": False}
    if ((not data['billId']) or data['billId'] == ''):
        return {"message": "Bill Id is required", "code": False}
    if ((not data['deskKot']) or data['deskKot'] == ''):
        return {"message": "Desk Kot is required", "code": False}
    if ((not data['tableType']) or data['tableType'] == ''):
        return {"message": "Table Type is required", "code": False}
    if ((not data['specialInstructions'])
            or data['specialInstructions'] == ''):
        return {"message": "Special Instructions is required", "code": False}
    if ((not data['totalQty']) or data['totalQty'] == ''):
        return {"message": "Total Qty is required", "code": False}
    if ((not data['taxes']) or data['taxes'] == ''):
        return {"message": "Taxes is required", "code": False}
    if ((not data['taxableAmount']) or data['taxableAmount'] == ''):
        return {"message": "Taxable Amount is required", "code": False}
    if ((not data['totalTax']) or data['totalTax'] == ''):
        return {"message": "Total Tax is required", "code": False}
    if ((not data['items']) or data['items'] == ''):
        return {"message": "Items is required", "code": False}
    if ((not data['printerName']) or data['printerName'] == ''):
        return {"message": "Printer Name is required", "code": False}
    if ((not data['kot']) or data['kot'] == ''):
        return {"message": "KOT is required", "code": False}
    if ((not data['kot']['kotNumber']) or data['kot']['kotNumber'] == ''):
        return {"message": "KOT Number is required", "code": False}
    if (not data['kot']['items'] or data['kot']['items'] == ''
            or len(data['kot']['items']) == 0):
        return {"message": "KOT Items are required", "code": False}
    for item in data['kot']['items']:
        if (not item):
            return {"message": "KOT Items are required", "code": False}
        if ((not item['itemName']) or item['itemName'] == ''):
            return {"message": "Item Name is required", "code": False}
        if ((not item['itemQty']) or item['itemQty'] == ''):
            return {"message": "Item Qty is required", "code": False}
        if ((not item['itemPrice']) or item['itemPrice'] == ''):
            return {"message": "Item Price is required", "code": False}
        if ((not item['itemTotal']) or item['itemTotal'] == ''):
            return {"message": "Item Total is required", "code": False}

    print(data)
    font = {
        "height": 8,
    }
    try:
        with win32printing.Printer(data['printerName'],
                                   'Bill - ' + date,
                                   auto_page=True) as printer:
            printer.text(data['hotelName'], font_config=font)

        return {"status": 'success'}
    except Exception as e:
        return {"status": 'error', "error": str(e)}


@app.route('/printBill', methods=['POST'])
def printBill():
    date = datetime.datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
    data = request.json
    print(data)
    font = {
        "height": 8,
    }
    try:
        with win32printing.Printer('Microsoft Print To PDF',
                                   'Bill - ' + date,
                                   auto_page=True) as printer:
            printer.text(data['hotelName'], font_config=font)
        return {"status": 'success'}
    except Exception as e:
        return {"status": 'error', "error": str(e)}


# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=8080, debug=True)
