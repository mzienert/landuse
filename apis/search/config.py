# Configuration for the search API

AVAILABLE_COLLECTIONS = {
    'la_plata_county_code': {
        'name': 'Land Use Code',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'La Plata County Land Use Code regulations'
    },
    'la_plata_assessor': {
        'name': 'Property Assessor Data',
        'model': 'intfloat/e5-large-v2',
        'dimensions': 1024,
        'description': 'Property assessment and ownership data'
    }
}