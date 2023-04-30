import pandas as pd
from datetime import datetime
from pathlib import Path
import json
from gapis.gsheets.sheetclient import SheetClient

SPREADSHEETID = "1fjcqm9dofRSI5-WsOHvxloOMSdIw_3dJ7KTkN4YMbz4"

def getSheetClient():
    return SheetClient()

class GSheetPipeline:
    def __init__(self) -> None:
        self.ids = None
        self.sheetclient = None
        self.sheetname = None
    
    def open_spider(self, spider):
        self._init_sheetclient()
        self.appendvalues = []
    
    def close_spider(self, spider):
        self._append_newvalues()
    
    def _init_sheetclient(self):
        self.sheetclient = getSheetClient()
        self.sheetname = "Sheet1"
        self._get_initial_sheet_values()
        self.ids = set(self._initvalues["id"])
    
    def _get_initial_sheet_values(self):
        self.lastcol = "S"
        columns = self.sheetclient.getSheetValues(
            spreadsheetId=SPREADSHEETID, 
            rangeName=f"{self.sheetname}!A1:{self.lastcol}1"
        )['values'][0]
        initvalues =  self.sheetclient.getSheetValues(
            spreadsheetId=SPREADSHEETID,
            rangeName=f"{self.sheetname}!A2:{self.lastcol}"
        )['values']
        self._initvalues = pd.DataFrame(
            columns=columns,
            data=initvalues
        )
    
    def _get_append_value(self, item):
        appendvalue = {}
        for k in self._initvalues.columns:
            if k not in item:
                appendvalue[k] = ""
            else:
                appendvalue[k] = item[k]
        return appendvalue
    
    def _append_newvalues(self):
        appendvalues = [list(item.values()) for item in self.appendvalues]
        Path(f"appendvalues_{datetime.now().strftime('%Y-%m-%d')}.json").write_text(
            json.dumps(appendvalues, indent=2)
        )
        print(f"Appending {len(appendvalues)} new rows to google sheet {SPREADSHEETID}")
        self.sheetclient.appendValuesToSheet(
            spreadsheetId=SPREADSHEETID, 
            rangeName=f"{self.sheetname}!A2:{self.lastcol}", 
            addvalues=appendvalues
        )