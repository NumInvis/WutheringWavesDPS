import XLSX from 'xlsx';
import fs from 'fs';
import path from 'path';

const workbook = XLSX.readFile(path.resolve('../WWAC.xlsx'));
const sheetName = workbook.SheetNames[0];
const worksheet = workbook.Sheets[sheetName];

const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

const headers = jsonData[2];
const data = [];

for (let i = 3; i < jsonData.length; i++) {
    const row = jsonData[i];
    if (row.length > 0 && row[0]) {
        const obj = {};
        for (let j = 0; j < headers.length; j++) {
            obj[headers[j]] = row[j];
        }
        data.push(obj);
    }
}

fs.writeFileSync(path.resolve('./public/wwac_data.json'), JSON.stringify(data, null, 2), 'utf8');
console.log(`Successfully converted ${data.length} records to wwac_data.json`);
