from django.shortcuts import redirect, render
from django.http import JsonResponse
# prevent unauthorized POST requests from malicious websites.
from django.views.decorators.csrf import csrf_exempt
# for making HTTP requests
import requests
# for working with JSON data
import json
#used for working with regular expressions
import re

from rest_framework.views import APIView

from mistral.forms import ChatbotForm, LoginForm
from mlmistral.settings import SECRET_KEY
from .serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User
import jwt,datetime
from functools import wraps
from django.utils.decorators import method_decorator




def token_required(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Token is missing!'}, status=403)

        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
                 # Print the token after extracting the actual JWT
            print("Token after split:", token)
            payload = jwt.decode(token, SECRET_KEY , algorithms=['HS256'])
            request.user_id = payload['id']
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired!'}, status=403)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token!'}, status=403)

        return f(request, *args, **kwargs)
    return decorated_function

# User Register
class Register(APIView):
    def post(self, request):
        serializer = UserSerializer(data= request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)



class Login(APIView):
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found')
        
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password')
        
        # exp : sets the expiration time claim for the JWT
        # iat : specifies the time at which the token was issued
        payload= {
            'id' : user.id,
            'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat' : datetime.datetime.utcnow()
        }

        # encodes the payload into a JSON Web Token (JWT) using the PyJWT
        # secret : secret key for encoding the token
        # The hashing algorithm used to generate the signature for the token
        # decode : used to convert token to a string
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        # create a response object
        response = Response()
        # set the token in cookies
        response.set_cookie(key='token', value=token, httponly=True)
        # return the token in the response body as well
        response.data = {'token': token}
        
        return response

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.filter(email=email).first()
            if user is None or not user.check_password(password):
                return render(request, 'login.html', {'form': form, 'error': 'Invalid email or password'})
            
            user_info = {
                'id': user.id,
                'email': user.email,
            }

            payload = {
                'user': user_info,
                'id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
                'iat': datetime.datetime.utcnow()
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            
            # Storing token in session and sending it as a JSON response
            request.session['token'] = token
            return JsonResponse({'token': token})
            
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})

    
# Define the URL of the Mistral API
OLLAMA_MISTRAL_API_URL = "http://localhost:11434/api/generate"
# Define the name of the model to be used
MODEL_NAME = "mistral"

# Function to transform text by removing newlines, backslashes, and joining words
def transform_text(input_text):
    transformed_text = input_text.replace('\n', ' ')
    transformed_text = transformed_text.replace('\\', '')
    transformed_text = re.sub(r'([A-Za-z]+)\s([A-Za-z]+)', r'\1\2', transformed_text)
    return transformed_text


# View to generate text using Mistral API
@csrf_exempt
@token_required
def generate_text(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            prompt = data.get('prompt')
            
            # Check if 'prompt' is missing in the request
            if not prompt:
                return JsonResponse({'error': 'Missing prompt'}, status=400)

            # Prepare payload for the API request
            payload = {
                'model': MODEL_NAME,
                'prompt': prompt
            }

            # Send a POST request to the Mistral API
            response = requests.post(OLLAMA_MISTRAL_API_URL, json=payload, stream=True)

            # Check if the API request was successful
            if response.status_code != 200:
                return JsonResponse({'error': f'API request failed with status code {response.status_code}'}, status=500)

            # Combine the response lines into a single string
            combined_response = ''
            for line in response.iter_lines():
                if line:
                    response_data = json.loads(line)
                    combined_response += response_data['response'] + ' '
            # Transform the combined response text
            transformed_response = transform_text(combined_response)
            
            # Return the transformed response as JSON
            return JsonResponse({'response': transformed_response.strip()}, status=200)

        except Exception as e:
            # Return an error response if an exception occurs
            return JsonResponse({'error': str(e)}, status=500)
    else:
        # Return an error response for non-POST requests
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    

def chatbot_view(request):
    if 'token' not in request.session:
        return redirect('login')
    # Retrieve the token from the session
    token = request.session['token']
    print("Token in chatbot_view:", token)
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    form = ChatbotForm()
    messages = request.session.get('messages', [])
    return render(request, 'chatbot.html', {'form': form, 'messages': messages, 'token': token})


def logout_view(request):
    # Clear the token from the session
    if 'token' in request.session:
        del request.session['token']
    
    # Redirect to the login page
    return redirect('login')