{% set my_dict = {
    'first_name': 'Nikolas',
    'last_name': 'Biniaris',
    'age': 27,
    'city': 'Stockholm'
} %}



My name is {{ my_dict['first_name']}}, 
my last name is {{ my_dict['last_name']}}, 
I am {{ my_dict['age']}} years old 
and I currently live in {{ my_dict['city']}}





{% for key, value in my_dict.items() %}
    {{ key }}: {{ value }}
{% endfor %}
    