
# Multi-Tenant E-Commerce Platform 


A Multi-tenant e-commerce backend where multiple vendors (tenants) can host their stores on a shared platform. Each vendor can manage their own products, orders, and customers independently, while sharing the same backend infrastructure. 


## Run Locally

Suggested compatible python version : Python 3.11, Python 3.10 

Clone the project

```bash
git clone https://github.com/Sa7yaC/ecommerce-platform.git
```

Go to the project directory

```bash
cd ecommerce-platform/backend
```

Create Virtual Environment

For windows:
```bash
python -m venv venv     
venv\Scripts\activate
```
For linux/mac:
```bash
python3 -m venv venv
source venv/bin/activate
```


Install dependencies

```bash
pip install -r requirements.txt
```

Database setup

```bash
python manage.py makemigrations
python manage.py migrate
```

Create Initial Tenant

```bash
python manage.py shell
```
In the Python shell:

```bash
from store.models import Tenant

tenant = Tenant.objects.create(
    name="",
    store_name="",
    contact_email="example@store.com",
    contact_phone="",
    subdomain=""
)

print(f"Tenant created with ID: {tenant.id}")
exit()
```

Start the server

```bash
python manage.py runserver
```

## API Endpoints

#### Register as customer/staff/store_owner

```http
POST /auth/register/
```

| JSON Key | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `username` | `varchar` | username |
| `email` | `email` | email |
| `password` | `varchar` | password |
| `password2` | `varchar` | confirm password |
| `first_name` | `varchar` | first name of the user |
| `last_name` | `varchar` | last name of the user |
| `phone` | `varchar` | phone number of the user |
| `address` | `varchar` | address of the user |
| `role` | `varchar` | role of the user |
| `tenant_id` | `int` | tenant id upon which registeration is occuring |

## As customer
#### Login

```http
POST /auth/login/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `username`      | `varchar` | username for login |
| `password`      | `varchar` | password for login |

#### Get products

```http
GET /products/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### Place order

```http
POST /orders/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `shipping address`      | `varchar` | shipping address for the user |
| `notes`      | `varchar` | any special mention |
| `product id`      | `int` | product id for the order placement |
| `product quantity`      | `int` | quantity of the product |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### View order history

```http
GET /orders/my_orders/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

## As staff
#### Login

```http
POST /auth/login/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `username`      | `varchar` | username for login |
| `password`      | `varchar` | password for login |

#### Add product

```http
POST /products/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `name`      | `varchar` | name of the product |
| `description`      | `varchar` | description of the product |
| `price`      | `decimal` | price of the product |
| `stock`      | `int` | total quantity of the product |
| `category`      | `varchar` | category of the product |
| `image link`      | `url` | image link of the product |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### View pending orders

```http
GET /orders/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### Update product

```http
PATCH /orders/{id}/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `name`      | `varchar` | name of the product |
| `description`      | `varchar` | description of the product |
| `price`      | `decimal` | price of the product |
| `stock`      | `int` | total quantity of the product |
| `category`      | `varchar` | category of the product |
| `image link`      | `url` | image link of the product |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### Update order status

```http
POST /orders/{id}/update_status/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `{id}`      | `int` | product id for the order status update |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

## As store owner
#### Login

```http
POST /auth/login/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `username`      | `varchar` | username for login |
| `password`      | `varchar` | password for login |

#### View all orders

```http
GET /orders/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### Assign staff

```http
POST /orders/{id}/assign_staff/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `{id}`      | `int` | product id for the staff to be assigned to |
| `staff id`      | `int` | staff id to assign order to |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |

#### Delete product

```http
DELETE /products/{id}/
```

| JSON Key | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `{id}`      | `int` | product id for the deletion |
| `access_token`      | `Bearer Token` | accesss token for confirmation of tenant and role |


## Short note

### Multi-tenancy:
The system uses one shared database for all stores. To keep each store’s data separate, every record (like users, products, and orders) is linked to a specific tenant using a tenant field. This makes sure that one store cannot see or access another store’s data, even though everything is stored in the same place.

### Role-based access:
The platform has a custom user model with three roles — store owner, staff, and customer. These roles decide what each user is allowed to do. Store owners can manage everything, staff can manage store operations, and customers can only place and view their own orders. The system checks the user’s role and tenant before allowing any action, ensuring that users only access information that belongs to their own store. 