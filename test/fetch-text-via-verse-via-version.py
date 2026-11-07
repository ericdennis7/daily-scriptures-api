from getbible import GetBible

bible = GetBible()

result = bible.select("John 3:16", "esv")
print(result)