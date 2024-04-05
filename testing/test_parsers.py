import vasp_parsers

def test_parse_incar():
    template_incar = {
        'VALUE1': 1,
        'VALUE2': 2,
        'VALUE3': 3
    }
    template_comments = [
        "Comment 1 with another # and = in it and also ! in it",
        "Comment 2",
        ""
    ]
    read_incar, read_comments = vasp_parsers.parse_incar('testing/test_INCAR')
    assert read_incar == template_incar
    assert read_comments == template_comments