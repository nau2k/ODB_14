# -*- coding: utf-8 -*-
{
    "name": "Vietnamese country states (Provinces)",
    "summary": "Vietnamese country states (Provinces)",
    "version": "1.0.1",
    "category": "Technical",
    "website": "https://www.odoobase.com/",
    "author": "DuyBQ",
    "depends": [
        "base",
    ],
    "data": [
        'security/ir.model.access.csv',

        "data/district_custom.xml",
        "data/ward.xml"
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
