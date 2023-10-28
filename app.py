import json
from flask import Flask, request, jsonify
import win32print
import datetime
import jinja2
import os
from flask_cors import CORS
import subprocess
# from weasyprint import HTML, CSS

version = '1.0.0'
app = Flask(__name__)
CORS(app)
environment = jinja2.Environment()
billTemplate = open('billTemplate.jinja','r').read()

kotTemplate = open('kotTemplate.jinja','r').read()

def getHtmlBody(data):
    stylePath = os.path.abspath('style.css')
    print("Joined",os.getcwd(),os.getcwd()+'\\fonts\Overpass_Mono\OverpassMono-VariableFont_wght.ttf')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Bill</title>
        <style>
            {open(stylePath, 'r').read().replace('%/font/%','./fonts/Overpass_Mono/OverpassMono-VariableFont_wght.ttf')}
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
            output = subprocess.check_output('wkhtmltopdf --page-width 72mm --page-height 297mm -B 0.5mm -L 0.5mm -R 0.5mm -T 0.5mm temp_kot.html "' + filename+'"',creationflags=0x08000000,stderr=subprocess.STDOUT, shell=True, timeout=3,universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e)
        filename = os.path.abspath(filename)
        print(filename)
        print('FoxitReader.exe /t "' + filename + '" "'+data['printer']+'"')
        subprocess.call('FoxitReader.exe /t "' + filename + '" "'+data['printer']+'"',
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
            output = subprocess.check_output('wkhtmltopdf --page-width 80mm --page-height 297mm -B 3mm -L 5mm -R 3mm -T 3mm temp_bill.html "' + filename+'"',creationflags=0x08000000,stderr=subprocess.STDOUT, shell=True, timeout=3,universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e)
        # print("Output",output)
        filename = os.path.abspath(filename)
        print('FoxitReader.exe /t ' + filename)
        subprocess.call('FoxitReader.exe /t "' + filename + '" "'+data['printer']+'"',
                        creationflags=0x08000000)
        subprocess.call('FoxitReader.exe /t "' + filename + '" "'+data['printer']+'"',
                        creationflags=0x08000000)
        return jsonify({"status": 'success'}), 200
    except Exception as e:
        return jsonify({"status": 'error', "error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
