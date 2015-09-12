import io
from zipfile import ZipFile

from nose.tools import istest, assert_equal

from mammoth.docx.style_map import write_style_map, read_style_map
from mammoth.zips import open_zip
from mammoth.docx import xmlparser as xml


@istest
def reading_embedded_style_map_on_document_without_embedded_style_map_returns_none():
    fileobj = _normal_docx()
    assert_equal(None, read_style_map(fileobj))


@istest
def writing_style_map_preserves_unrelated_files():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    with open_zip(fileobj, "r") as zip_file:
        assert_equal("placeholder", zip_file.read_str("placeholder"))

@istest
def embedded_style_map_can_be_read_after_being_written():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    assert_equal("p => h1", read_style_map(fileobj))


@istest
def embedded_style_map_is_written_to_separate_file():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    with open_zip(fileobj, "r") as zip_file:
        assert_equal("p => h1", zip_file.read_str("mammoth/style-map"))


@istest
def embedded_style_map_is_referenced_in_relationships():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    assert_equal(expected_relationships_xml, _read_relationships_xml(fileobj))


@istest
def can_overwrite_existing_style_map():
    fileobj = _normal_docx()
    write_style_map(fileobj, "p => h1")
    write_style_map(fileobj, "p => h2")
    with open_zip(fileobj, "r") as zip_file:
        assert_equal("p => h2", read_style_map(fileobj))
        _assert_no_duplicates(zip_file._zip_file.namelist())
        assert_equal(expected_relationships_xml, _read_relationships_xml(fileobj))


def _read_relationships_xml(fileobj):
    with open_zip(fileobj, "r") as zip_file:
        return xml.parse_xml(
            io.StringIO(zip_file.read_str("word/_rels/document.xml.rels")),
            [("r", "http://schemas.openxmlformats.org/package/2006/relationships")],
        )


original_relationships_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>' +
    '</Relationships>')

expected_relationships_xml = xml.element("r:Relationships", {}, [
    xml.element("r:Relationship", {"Id": "rId3", "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings", "Target": "settings.xml"}),
    xml.element("r:Relationship", {"Id": "rMammothStyleMap", "Type": "http://schemas.zwobble.org/mammoth/style-map", "Target": "/mammoth/style-map"}),
])


def _normal_docx():
    fileobj = io.BytesIO()
    zip_file = ZipFile(fileobj, "w")
    try:
        zip_file.writestr("placeholder", "placeholder")
        zip_file.writestr("word/_rels/document.xml.rels", original_relationships_xml)
        expected_relationships_xml
    finally:
        zip_file.close()
    return fileobj


def _assert_no_duplicates(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    for value, count in counts.items():
        if count != 1:
            assert False, "{0} has count of {1}".format(value, count)