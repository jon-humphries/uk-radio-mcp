from uk_radio_mcp import export


def test_make_tag():
    assert export.make_tag("Acme Limited") == "Acme"
    assert export.make_tag("TORBAY AND SOUTH DEVON NHS FOUNDATION TRUST") == "Torbay And South"
    assert len(export.make_tag("x" * 40)) == 16
    assert export.make_tag("  ") == "Unknown"


def test_write_whistler(tmp_path):
    p = export.write_whistler([(453.15, "Anglo Beef"), (459.65, 'Say "hi"')], tmp_path / "o.csv")
    raw = p.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    assert text.split("\r\n")[0] == "Alpha Tag,Frequency,Mode"
    assert '"Anglo Beef",453.1500,AUTO' in text
    assert '"Say hi",459.6500,AUTO' in text
