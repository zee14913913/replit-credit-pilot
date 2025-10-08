import re

CATEGORY_KEYWORDS = {
    'Food & Dining': [
        'restaurant', 'cafe', 'coffee', 'mcdonald', 'kfc', 'pizza', 'burger', 
        'food', 'dining', 'starbucks', 'bakery', 'kitchen', 'bistro', 'eatery',
        'mamak', 'nasi', 'roti', 'makan', 'kopitiam', 'steamboat', 'sushi'
    ],
    'Transport': [
        'grab', 'uber', 'taxi', 'petrol', 'fuel', 'parking', 'toll', 'tnb',
        'shell', 'petronas', 'brt', 'lrt', 'mrt', 'bus', 'train', 'transportation',
        'motorcycle', 'car wash', 'automotive'
    ],
    'Shopping': [
        'mall', 'shopping', 'store', 'boutique', 'fashion', 'clothing', 'shoes',
        'lazada', 'shopee', 'amazon', 'ikea', 'aeon', 'pavilion', 'mid valley',
        'suria', 'purchase', 'retail'
    ],
    'Groceries': [
        'supermarket', 'grocery', 'tesco', 'giant', 'jaya', 'market', 'fresh',
        'village grocer', '99 speedmart', 'mydin', 'econsave'
    ],
    'Bills & Utilities': [
        'electric', 'water', 'internet', 'telco', 'bill', 'utility', 'astro',
        'unifi', 'maxis', 'digi', 'celcom', 'yes', 'syabas', 'air selangor',
        'tenaga nasional', 'indah water'
    ],
    'Entertainment': [
        'cinema', 'movie', 'netflix', 'spotify', 'disney', 'game', 'entertainment',
        'gsc', 'tgv', 'concert', 'show', 'theater', 'streaming'
    ],
    'Healthcare': [
        'clinic', 'hospital', 'pharmacy', 'medical', 'doctor', 'health', 'dental',
        'guardian', 'watsons', 'caring', 'klinik', 'farmasi'
    ],
    'Online Services': [
        'google', 'apple', 'microsoft', 'subscription', 'digital', 'online',
        'cloud', 'software', 'app store', 'play store'
    ],
    'Travel': [
        'hotel', 'airasia', 'malaysia airlines', 'flight', 'travel', 'booking',
        'agoda', 'airbnb', 'resort', 'airline', 'mas', 'airport'
    ],
    'Insurance': [
        'insurance', 'takaful', 'prudential', 'aia', 'great eastern', 'allianz'
    ],
    'Others': []
}

def categorize_transaction(description):
    description_lower = description.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description_lower:
                confidence = 0.9 if len(keyword) > 5 else 0.7
                return category, confidence
    
    return 'Others', 0.5

def validate_statement(statement_total, transactions):
    if not transactions:
        return {
            'is_valid': False,
            'confidence': 0,
            'inconsistencies': ['No transactions found'],
            'calculated_total': 0,
            'difference': statement_total
        }
    
    calculated_total = sum(t['amount'] for t in transactions)
    difference = abs(statement_total - calculated_total)
    tolerance = 0.01
    
    is_valid = difference <= tolerance
    confidence = 1.0 if is_valid else max(0, 1.0 - (difference / statement_total))
    
    inconsistencies = []
    if not is_valid:
        inconsistencies.append(f"Total mismatch: Statement={statement_total:.2f}, Calculated={calculated_total:.2f}, Diff={difference:.2f}")
    
    missing_dates = [t for t in transactions if not t.get('date')]
    if missing_dates:
        inconsistencies.append(f"{len(missing_dates)} transactions missing dates")
    
    missing_amounts = [t for t in transactions if not t.get('amount') or t.get('amount') == 0]
    if missing_amounts:
        inconsistencies.append(f"{len(missing_amounts)} transactions missing amounts")
    
    return {
        'is_valid': is_valid,
        'confidence': round(confidence, 2),
        'inconsistencies': inconsistencies,
        'calculated_total': calculated_total,
        'difference': difference
    }

def get_spending_summary(transactions):
    summary = {}
    
    for trans in transactions:
        category = trans.get('category', 'Others')
        amount = trans.get('amount', 0)
        
        if category not in summary:
            summary[category] = {
                'total': 0,
                'count': 0,
                'transactions': []
            }
        
        summary[category]['total'] += amount
        summary[category]['count'] += 1
        summary[category]['transactions'].append({
            'date': trans.get('date'),
            'description': trans.get('description'),
            'amount': amount
        })
    
    sorted_summary = dict(sorted(summary.items(), key=lambda x: x[1]['total'], reverse=True))
    return sorted_summary
