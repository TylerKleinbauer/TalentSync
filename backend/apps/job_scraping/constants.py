EMPLOYMENT_POSITION_CHOICES = {
    1: "executive_position",
    2: "position_with_responsibilities",
    3: "employee",
}

EMPLOYMENT_TYPE_CHOICES = {
    1: "temporary",
    2: "freelance",
    3: "internship",
    4: "supplementary_income",
    5: "permanent_position",
    6: "apprenticeship",
}

INDUSTRIES = {
    1: {
        'FR': "Construction d'installations / de machines et construction métallique",
        'EN': "Plant / Machine / Metal construction",
    },
    2: {
        'FR': "Aéronautique / Logistique / Transport / Mobilité",
        'EN': "Aviation / Logistics / Transport / Traffic",
    },
    3: {
        'FR': "Banques",
        'EN': "Banking",
    },
    4: {
        'FR': "Bâtiment / Immobilier",
        'EN': "Construction industry / Real estate",
    },
    5: {
        'FR': "Vêtements / Textile",
        'EN': "Clothing / Textiles",
    },
    6: {
        'FR': "Enseignement",
        'EN': "Education system",
    },
    7: {
        'FR': "Biotechnologie / Chimie / Pharmaceutique",
        'EN': "Biotechnology / Chemistry / Pharmaceutical",
    },
    8: {
        'FR': "Commerce de détail",
        'EN': "Retail business",
    },
    9: {
        'FR': "Services",
        'EN': "Services",
    },
    10: {
        'FR': "E-business / Internet",
        'EN': "E-business / Internet",
    },
    11: {
        'FR': "Electronique / Electrotechnique",
        'EN': "Electronics / Electrotechnical",
    },
    12: {
        'FR': "Alimentation en énergie / en eau",
        'EN': "Power / Water supply",
    },
    13: {
        'FR': "Traitement des déchets / Environnement / Techniques antipollution",
        'EN': "Waste management / Recycling / Environmental technology",
    },
    14: {
        'FR': "Marché automobile",
        'EN': "Automotive market",
    },
    15: {
        'FR': "Horlogerie / Optique / Mécanique de précision",
        'EN': "Precision mechanics / Optics / Watch and clock industry",
    },
    16: {
        'FR': "Finance / Comptabilité",
        'EN': "Finance / Accounting",
    },
    17: {
        'FR': "Recherche et sciences",
        'EN': "Science and research",
    },
    18: {
        'FR': "Sylviculture / agriculture",
        'EN': "Forestry / Agriculture",
    },
    19: {
        'FR': "Loisirs / Culture / Sport",
        'EN': "Leisure / Culture / Sports",
    },
    20: {
        'FR': "Hôtellerie / Restauration / Tourisme",
        'EN': "Catering / Hotel business / Tourism",
    },
    21: {
        'FR': "Agroalimentaire",
        'EN': "Agri-food industry",
    },
    22: {
        'FR': "Santé",
        'EN': "Healthcare",
    },
    23: {
        'FR': "Petites et moyennes industries",
        'EN': "Small and medium-sized industries",
    },
    24: {
        'FR': "Industrie du verre / du plastique / du papier",
        'EN': "Glass / Plastic / Paper industry",
    },
    25: {
        'FR': "Industrie graphique / Médias / Edition",
        'EN': "Graphic industry / Media / Publishing",
    },
    26: {
        'FR': "Commerce de gros",
        'EN': "Wholesale",
    },
    27: {
        'FR': "Ressources humaines / Service du personnel",
        'EN': "Human resources / Personnel services",
    },
    28: {
        'FR': "Industries (autres industries)",
        'EN': "Industry (other industries)",
    },
    29: {
        'FR': "Informatique",
        'EN': "IT",
    },
    30: {
        'FR': "Communication / Marketing / RP / Publicité",
        'EN': "Communications / Marketing / PR / Advertising",
    },
    31: {
        'FR': "Technique médicale",
        'EN': "Medical technology",
    },
    32: {
        'FR': "Administration publique",
        'EN': "Public administration",
    },
    33: {
        'FR': "Droit",
        'EN': "Law",
    },
    34: {
        'FR': "Affaires sociales",
        'EN': "Welfare system",
    },
    35: {
        'FR': "Télécommunications",
        'EN': "Telecommunications",
    },
    36: {
        'FR': "Conseil aux entreprises",
        'EN': "Consultancy",
    },
    37: {
        'FR': "Associations / Organisations",
        'EN': "Associations / Organisations",
    },
    38: {
        'FR': "Assurances",
        'EN': "Insurance",
    },
    39: {
        'FR': "Métiers divers",
        'EN': "Miscellaneous",
    },
}

def fetch_industries(lang: str = 'EN') -> list:
    """
    Returns a list of tuples containing industry identifiers and their names in the specified language.
    
    Args:
        lang (str): Language code to use ('EN' or 'FR').
    
    Returns:
        list: A sorted list of tuples, each of the form (id, industry_name).
    """
    industries = []
    for industry_id, details in INDUSTRIES.items():
        name = details.get(lang, "")
        industries.append((industry_id, name))
    # Sort the list by the industry id (or any other criteria if desired)
    industries.sort(key=lambda x: x[0])
    return industries
