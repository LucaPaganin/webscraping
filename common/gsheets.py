import pandas as pd
from datetime import datetime
from pathlib import Path
import json
from gapis.gsheets.sheetclient import SheetClient

SPREADSHEETID = "1fjcqm9dofRSI5-WsOHvxloOMSdIw_3dJ7KTkN4YMbz4"

def getSheetClient():
    return SheetClient()

class ImmobSheetclient(SheetClient):
    def __init__(self, spreadsheetId=None, sheetName="Sheet1", **kwargs) -> None:
        super().__init__(**kwargs)
        self.spreadsheetId = spreadsheetId if spreadsheetId else SPREADSHEETID
        self.sheetName = sheetName
        self.lastcol = "AZ"
    
    def getSheetValues(self, rangeName):
        return super().getSheetValues(self.spreadsheetId, rangeName)
    
    def appendValuesToSheet(self, rangeName, addvalues):
        return super().appendValuesToSheet(self.spreadsheetId, rangeName, addvalues)
    
    def batchUpdate(self, rangeName, values, majorDimension, valueInputOption="RAW"):
        return super().batchUpdate(self.spreadsheetId, rangeName, values, majorDimension, valueInputOption)
    
    def getSheetDataframe(self):
        columns = self.getSheetValues(
            f"{self.sheetName}!A1:{self.lastcol}1"
        )['values'][0]
        columns = [c for c in columns if c]
        data = self.getSheetValues(
            rangeName=f"{self.sheetName}!A2:{self.lastcol}"
        )['values']
        data = [
            d[:len(columns)] for d in data
        ]
        df = pd.DataFrame(data=data, columns=columns)
        return df[df["quartiere"] != ""]
    
    def updateSheetFromDataframe(self, df):
        data = df.to_numpy().tolist()
        self.batchUpdate(f"A2:{self.lastcol}", data, "ROWS")
    

    

class GSheetPipeline:
    def __init__(self) -> None:
        self.ids = None
        self.sheetclient = ImmobSheetclient()
        self.sheetname = None
        self.appendvalues = []
        self._initvalues = None
    
    def open_spider(self, spider):
        self._init_sheetclient()
    
    def close_spider(self, spider):
        self._append_newvalues()
    
    def _init_sheetclient(self):
        self._initvalues = self.sheetclient.getSheetDataframe()
        self.ids = set(self._initvalues["id"])
    
    def _get_append_value(self, item):
        appendvalue = {}
        for k in self._initvalues.columns:
            if k not in item:
                appendvalue[k] = ""
            else:
                appendvalue[k] = item[k]
        return appendvalue
    
    def _append_newvalues(self):
        now = datetime.now().date()
        appendvalues = [
            list(item.values()) for item in self.appendvalues
            if datetime.strptime(item['data'], "%d/%m/%Y").date() >= now
        ]
        Path(f"appendvalues_{datetime.now().strftime('%Y-%m-%d')}.json").write_text(
            json.dumps(appendvalues, indent=2)
        )
        print(f"Appending {len(appendvalues)} new rows to google sheet {SPREADSHEETID}")
        lastindex = len(self._initvalues)+1
        self.sheetclient.appendValuesToSheet(
            rangeName=f"{self.sheetname}!A{lastindex}:{self.sheetclient.lastcol}", 
            addvalues=appendvalues
        )