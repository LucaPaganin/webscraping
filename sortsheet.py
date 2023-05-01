from common.gsheets import ImmobSheetclient


if __name__ == '__main__':
    sc = ImmobSheetclient()
    df = sc.getSheetDataframe()
    df.sort_values(["quartiere", "via", "piano"], inplace=True, ignore_index=True)
    sc.updateSheetFromDataframe(df)

