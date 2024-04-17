# One-Product E-commerce Site with Django, htmx, and Stripe

This repository contains the full code for a step-by-step guide on how to build a one-product e-commerce site using Django, htmx, and Stripe:

- [part 1]() - configuring the Django project and integrating it with htmx for front-end interactivity
- [part 2]() - handle orders using Stripe.

## Setup Instructions

Before you can run this project, you'll need to set up your environment. Follow these steps:

1. Clone this repository to your local machine using `git clone github.com/franciscobmacedo/ecommerce-site`.
2. Navigate to the project directory.
3. Create a virtual environment using `python -m venv .venv`.
4. Activate the virtual environment. On Windows, use `.venv\\Scripts\\activate`. On Unix or MacOS, use `source .venv/bin/activate`.
5. Install the required packages using `pip install -r requirements.txt`.
6. Run the Django migrations using `python manage.py migrate`
7. Run the Django server using `python manage.py runserver`.
8. Navigate to `http://127.0.0.1:8000/` in your browser to see the site.
9. Set up the environment variables (like specified in the `.env.example`) file. Check the [part 2 of the guide]() for more details.

Please note, this project is just an example and is not intended for production use. For any queries or issues, please refer to the guide or raise an issue in this repository.
