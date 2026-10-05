"""Original educational content; explanations stay tied to these lesson cards."""
LESSONS = {
    'rights': {
        'title': 'Rights and constitutional remedies', 'subject': 'Polity', 'minutes': 4,
        'goal': 'Distinguish equality before law, constitutional remedies and directive principles.',
        'cards': [
            {'heading': 'Equality has two parts', 'text': 'Article 14 guarantees equality before the law and equal protection of the laws. Equal protection permits reasonable classification; it does not mean every person must receive identical treatment in every circumstance.'},
            {'heading': 'A remedy makes a right actionable', 'text': 'Article 32 provides the right to move the Supreme Court for enforcement of fundamental rights. Article 226 gives High Courts writ jurisdiction for enforcement of fundamental rights and for other purposes.'},
            {'heading': 'Different constitutional jobs', 'text': 'Fundamental rights are enforceable in court. Directive Principles of State Policy guide governance but are not enforceable by any court, under Article 37.'}
        ],
        'questions': [
            {'id': 'r1', 'prompt': 'Which statement best describes Article 14?', 'options': ['Identical treatment in every situation', 'Equality before law and equal protection of laws', 'Only a right to approach the Supreme Court'], 'answer': 1, 'concept': 'Reasonable classification', 'explanation': 'Article 14 contains both guarantees. Reasonable classification can be consistent with equal protection.', 'card': 0},
            {'id': 'r2', 'prompt': 'Which provision expressly guarantees moving the Supreme Court to enforce fundamental rights?', 'options': ['Article 32', 'Article 37', 'Article 226'], 'answer': 0, 'concept': 'Constitutional remedies', 'explanation': 'Article 32 is the constitutional remedy before the Supreme Court. Article 226 concerns High Courts and has a broader purpose.', 'card': 1},
            {'id': 'r3', 'prompt': 'Which statement about Directive Principles is correct?', 'options': ['They are enforceable just like fundamental rights', 'They apply only to the Supreme Court', 'They guide governance but are not enforceable by courts'], 'answer': 2, 'concept': 'Rights versus principles', 'explanation': 'Article 37 states that Directive Principles are not enforceable by courts, while remaining fundamental in governance.', 'card': 2}
        ],
        'source': 'https://legislative.gov.in/constitution-of-india/'
    },
    'inflation': {
        'title': 'Inflation without the jargon', 'subject': 'Economy', 'minutes': 3,
        'goal': 'Separate price levels, inflation rates and purchasing power.',
        'cards': [
            {'heading': 'A rate is not a level', 'text': 'Inflation is the rate at which the general price level rises over a period. If inflation falls from 6% to 4%, prices can still rise: they are rising more slowly. That is disinflation.'},
            {'heading': 'A basket tracks many prices', 'text': 'A consumer price index tracks the price of a representative basket of consumer goods and services. A change in one item alone does not necessarily equal economy-wide inflation.'},
            {'heading': 'Money and purchasing power', 'text': 'If your nominal income stays fixed while the general price level rises, your purchasing power falls. Deflation means a fall in the general price level, distinct from slower positive inflation.'}
        ],
        'questions': [
            {'id': 'i1', 'prompt': 'Inflation falls from 6% to 4%. What can this mean?', 'options': ['Prices are rising more slowly', 'All prices have fallen by 2%', 'Purchasing power must have increased'], 'answer': 0, 'concept': 'Disinflation versus deflation', 'explanation': 'A smaller positive inflation rate means the general price level still rises, but more slowly.', 'card': 0},
            {'id': 'i2', 'prompt': 'What does a consumer price index track?', 'options': ['Only the price of fuel', 'A representative consumer basket', 'Only exports'], 'answer': 1, 'concept': 'Price baskets', 'explanation': 'A consumer basket combines multiple goods and services; one item is not the whole index.', 'card': 1},
            {'id': 'i3', 'prompt': 'With fixed nominal income and rising prices, purchasing power generally…', 'options': ['rises', 'stays identical', 'falls'], 'answer': 2, 'concept': 'Purchasing power', 'explanation': 'The same nominal income buys less when the general price level rises.', 'card': 2}
        ],
        'source': 'https://www.imf.org/en/Publications/fandd/issues/Series/Back-to-Basics/Inflation'
    }
}

def public_lessons():
    return [{**{k: v for k, v in lesson.items() if k != 'questions'}, 'id': lid,
             'questions': [{k: v for k, v in q.items() if k in ('id', 'prompt', 'options')} for q in lesson['questions']]}
            for lid, lesson in LESSONS.items()]
