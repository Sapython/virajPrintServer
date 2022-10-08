import json
from flask import Flask, request, jsonify
import win32print
import datetime
import jinja2
import os
from flask_cors import CORS
import subprocess
from weasyprint import HTML, CSS

version = '1.0.0'
app = Flask(__name__)
CORS(app)
environment = jinja2.Environment()
billTemplate = '''
<div id="bill">
    <h3 style="text-align: center;font-style:bold;">{{currentBill['currentProject']['projectName']}}</h3>
    {% if currentBill['currentProject']['address'] %}
        <h4 style="text-align: center"> {{currentBill['currentProject']['address']}}</h4>
    {% endif %}
    {% if currentBill['currentProject']['phoneNumber'] %}
        <h4 style="text-align: center">Phone: {{currentBill['currentProject']['phoneNumber']}}</h4>
    {% endif %}
    {% if currentBill['isNonChargeable'] %}
    <hr>
        <h4 style="text-align:center;">COMPLIMENTARY BILL</h4>
        <h5>{{currentBill['complimentaryName']}}</h5>
    <hr>
    {% endif %}
        {% if currentBill['paymentMethod']=='cash' %}<div class="topFields">Paid With Cash</div> {% endif %}
        {% if currentBill['paymentMethod']=='card' %}<div class="topFields">Paid With Card</div> {% endif %}
        {% if currentBill['paymentMethod']=='dineIn' %}<div class="topFields">Dine In</div> {% endif %}
        {% if currentBill['paymentMethod']=='pickUp' %}<div class="topFields">Pick Up</div> {% endif %}
    <hr>
    {% if currentBill['currentProject']['gstNumber'] %}
        <div class="row">
            <div class="topFields">GST No.{{currentBill['currentProject']['gstNumber']}}</div>
            <div class="topFields">Date.{{currentBill['date']}}</div>
        </div>
    {% endif %}
    {% if currentBill['currentProject']['fssaiNo'] %}
        <div class="topFields">FSSAI No.{{currentBill['currentProject']['fssaiNo']}}</div>
    {% endif %}
    {% if currentBill['currentProject']['counterNo'] %}
        <div class="topFields">Counter No.{{currentBill['currentProject']['counterNo']}}</div>
    {% endif %}
    {% if currentBill['currentProject']['cashierName'] %}
        <div class="topFields">Cashier.{{currentBill['currentProject']['cashierName']}}</div>
    {% endif %}
    {% if currentBill['currentProject']['deviceName'] %}
        <div class="topFields">Device Name.{{currentBill['currentProject']['deviceName']}}</div>
    {% endif %}
    <div class="row">
        <div class="topFields">Bill No: {{currentBill['billNo']}}</div>
        <div class="topFields">Time:{{currentBill['time']}}</div>
    </div>
    {% if currentBill['customerInfoForm']['fullName'] %}
    <h4 style="text-align: start">Name:
        {{currentBill['customerInfoForm']['fullName']}}</h4>
    {% endif %}
    {% if currentBill['customerInfoForm']['phoneNumber'] %}
    <h4 style="text-align: start">Phone:
        {{currentBill['customerInfoForm']['phoneNumber']}}</h4>
    {% endif %}
    <div class="row">
        <h4 class="kotTokens">KOTs: <span class="breakWord">{{currentBill['kotsToken']}}</span></h4>
        {% if currentBill['currentTable']['type']=='table' %}
            <h4><b>Table No.:</b> {{currentBill['currentTable']['tableNo']}}</h4>
        {% endif %}
        {% if currentBill['currentTable']['type']=='room' %}
            <h4><b>Room No.:</b> {{currentBill['currentTable']['tableNo']}}</h4>
        {% endif %}
    </div>
    <table>
        <tr>
            <th>Product</th>
            <th>Qty</th>
            <th>Rate</th>
            <th>Amt</th>
        </tr>
        {% for product in currentBill['allProducts'] %}
            <tr>
                <td>{{product['dishName']}}</td>
                <td>{{product['quantity']}}</td>
                <td>{{product['shopPrice']}}</td>
                <td>{{product['shopPrice'] * product['quantity']}}</td>
            </tr>
        {% endfor %}
    </table>
    {% if specialInstructions %}
        <p class="info">Special Instructions: {{currentBill['specialInstructions']}}</p>
        <hr>
    {% endif %}
    <hr>
    <div class="info">
        <p>Total Qty: {{currentBill['totalQuantity']}}</p>
        <p>Sub Total: &#8377;{{currentBill['taxableValue']}}</p>
    </div>
    {% if (currentBill['selectDiscounts']|length) > 0 %}
        <hr>
        {% for discount in currentBill['selectDiscounts'] %}
            <div class="tax">
                <p>{{discount['title']}}</p>
                <p>{{discount['discountValue']}}</p>
                <p>{{discount['appliedDiscountValue']}}</p>
            </div>
        {% endfor %}
    {% endif %}
    <div class="tax">
        <p>CGST</p>
        <p>%2.5</p>
        <p>&#8377;{{currentBill['cgst']}}</p>
    </div>
    <div class="tax">
        <p>SGST</p>
        <p>%2.5</p>
        <p>&#8377;{{currentBill['sgst']}}</p>
    </div>
    <hr>
    <div class="total">
        <p>Total</p>
        <p>&#8377;{{currentBill['grandTotal']}}</p>
    </div>
    <p class="detail">*Net Total Inclusive of GST</p>
    <hr>
    {% if currentBill['customerInfoForm'] %}
        {% if currentBill['customerInfoForm']['name'] %} <p>Name: {{currentBill['customerInfoForm']['name']}}</p> {% endif %}
        {% if currentBill['customerInfoForm']['email'] %} <p>Mail: {{currentBill['customerInfoForm']['email']}}</p> {% endif %}
        {% if currentBill['customerInfoForm']['phone'] %} <p>Ph: {{currentBill['customerInfoForm']['phone']}}</p> {% endif %}
        {% if currentBill['customerInfoForm']['address'] %} <p>Add: {{currentBill['customerInfoForm']['address']}}</p> {% endif %}
    {% endif %}
    <hr>
    <p class="thanking">Thanks for visiting {{ currentBill['projectName'] }}</p>
    <p class="thanking">{{ currentBill['website'] }}</p>
</div>
'''

kotTemplate = '''
<div id="billKot">
    <h3 style="text-align: center">{{currentBill['currentProject']['projectName']}}</h3>
    <h4 style="text-align: center">{{currentBill['date']}}</h4>
    <h4 style="text-align: center">Bill Id: {{currentBill['billNo']}}</h4>
    {% if currentBill['isNonChargeable'] %}
        <h3>Non Chargeable</h3>
    {% endif %}
    {% if currentBill['cancelled'] %}
        <h3>Cancelled</h3>
    {% endif %}
    {% if currentBill['mode']=='edited' %}
        <h3>Modified</h3>
    {% endif %}
    <div class="row">
        <p class="kotTokens">Token: <span class="breakWord">{{currentBill['tokenNo']}}</span></p>
        {% if currentBill['currentTable']['type']=='table' %}
            <p><b>Table No.:</b> {{currentBill['currentTable']['tableNo']}}</p>
        {% endif %}
        {% if currentBill['currentTable']['type']=='room' %}
            <p><b>Room No.:</b> {{currentBill['currentTable']['tableNo']}}</p>
        {% endif %}
    </div>
    {% if currentBill['cancelled'] %}
    <table>
        <tr>
            <th>Product</th>
            <th>Ins.</th>
            <th>Qty</th>
        </tr>
        {% for product in currentBill['allProducts'] %}
            <tr>
                <td><del>{{product['dishName']}}</del></td>
                <td class="ins"><del>{{product['instruction']}}</del></td>
                <td><del>{{product['quantity']}}</del></td>
            </tr>
        {% endfor %}
    </table>
    {% endif %}
    {% if not currentBill['cancelled'] %}
    <table>
        <tr>
            <th>Product</th>
            <th>Ins.</th>
            <th>Qty</th>
        </tr>
        {% for product in currentBill['allProducts'] %}
            <tr>
                <td>{{product['dishName']}}</td>
                <td class="ins">{{product['instruction']}}</td>
                <td>{{product['quantity']}}</td>
            </tr>
        {% endfor %}
        {% for product in currentBill['deleted'] %}
            <tr>
                <td><del>{{product['dishName']}}</del></td>
                <td class="ins"><del>{{product['instruction']}}</del></td>
                <td><del>{{product['quantity']}}</del></td>
            </tr>
        {% endfor %}
    </table>
    {% endif %}
    <hr>
    {% if specialInstructions %}
        <p class="info">Special Instructions: {{currentBill['specialInstructions']}}</p>
    {% endif %}
</div>
'''

def getHtmlBody(data):
    stylePath = os.path.abspath('style.css')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Bill</title>
        <style>
            {open(stylePath, 'r').read().replace('%/font/%',os.path.abspath('/fonts/Space_Mono/SpaceMono-Regular.ttf'))}
        </style>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@200;400;500;600;700&display=swap" rel="stylesheet"> 
    </head>
    <body>
    {data}
    </body>
    '''

data = {
    'hotelName': 'Hotel Name',
    'today': datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
    'billId': '97592839832',
    'deskKot': True,
    'tokenNo': 'Token No',
    'tableNo': '2',
    'tableType': 'table',
    'allProducts': [{
        'dishName': 'Dish Name',
        'quantity': '2'
    }],
    'specialInstructions': 'Special Instructions'
}


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
    print(data)
    try:
        billInstance = environment.from_string(getHtmlBody(kotTemplate))
        data['date'] = datetime.datetime.now().strftime("%d/%m/%Y %I:%M %p")
        index = 0
        for item in data['allProducts']:
            data['allProducts'][index]['dishName'] = item['dishName'].capitalize()
            index+=1
        compiledKot= billInstance.render(
            currentBill=data
        )
        with open('temp_kot.html', 'w') as f:
            f.write(compiledKot)
        date = datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        print(f'kots/kot_{date}.pdf')
        filename = f'kots/kot_{date}.pdf'
        # HTML(string=compiledKot).write_pdf(
        #     filename, stylesheets=[CSS(filename='style.css')])
        try:
            output = subprocess.check_output('wkhtmltopdf --page-width 72mm --page-height 297mm -B 3mm -L 3mm -R 5mm -T 3mm temp_kot.html "' + filename+'"',creationflags=0x08000000,stderr=subprocess.STDOUT, shell=True, timeout=3,universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e)
        filename = os.path.abspath(filename)
        print(filename)
        print('FoxitReader.exe /t "' + filename + '" '+data['printer'])
        subprocess.call('FoxitReader.exe /t "' + filename + '" '+data['printer'],
                        creationflags=0x08000000)
        # subprocess.call('FoxitReader.exe /t "' + filename + '" '+data['printer'],
        #                 creationflags=0x08000000)
        return jsonify({"status": 'success'}), 200
    except Exception as e:
        return jsonify({"status": 'error', "error": str(e)}), 400

@app.route('/printBill', methods=['POST'])
def printBill():
    date = datetime.datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
    data = request.json
    print(data)
    try:
        billInstance = environment.from_string(getHtmlBody(billTemplate))
        data['date'] = datetime.datetime.now().strftime("%d/%m/%Y")
        data['time'] = datetime.datetime.now().strftime("%I:%M %p")
        index = 0
        for item in data['allProducts']:
            data['allProducts'][index]['dishName'] = item['dishName'].capitalize()
            index+=1
        with open('incoming.json','w+') as fs:
            fs.write(json.dumps(data))
        compiledKot= billInstance.render(
            currentBill=data
        )
        with open('temp_bill.html', 'w') as f:
            f.write(compiledKot)
        date = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
        print(f'kots/bill_{date}.pdf')
        filename = f'bills/bill_{date}.pdf'
        # HTML(string=compiledKot).write_pdf(
        #     filename, stylesheets=[CSS(filename='style.css')])
        try:
            output = subprocess.check_output('wkhtmltopdf --page-width 80mm --page-height 297mm -B 3mm -L 3mm -R 3mm -T 3mm temp_bill.html "' + filename+'"',creationflags=0x08000000,stderr=subprocess.STDOUT, shell=True, timeout=3,universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e)
        # print("Output",output)
        filename = os.path.abspath(filename)
        print('FoxitReader.exe /t ' + filename)
        subprocess.call('FoxitReader.exe /t "' + filename + '" '+data['printer'],
                        creationflags=0x08000000)
        subprocess.call('FoxitReader.exe /t "' + filename + '" '+data['printer'],
                        creationflags=0x08000000)
        return jsonify({"status": 'success'}), 200
    except Exception as e:
        return jsonify({"status": 'error', "error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
