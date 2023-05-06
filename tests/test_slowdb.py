import requests


def test_slowdb():
    """
    Test the slowdb endpoints
    :return: 10 if pass, 0 if fail
    """
    try:
        requests.delete('http://localhost:8000/clear')
        # Test the PUT endpoint
        data = {'key': 'one', 'value': '1'}
        response = requests.put('http://localhost:8000/put', json=data)
        assert response.status_code == 200 and response.json() == {'result': 'success'}

        # Test the GET endpoint
        response = requests.get('http://localhost:8000/get?key=one')
        assert response.status_code == 200 and response.json() == {'key': 'one', 'value': '1'}
        return 10
    except:
        return 0
