# Setup ===========================================================================================

# Import
import flask
import flask_sqlalchemy
import datetime
from productDictionary import *

# Setup website
main_website = flask.Flask(__name__, template_folder = "template")
main_website.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ordering.db"
main_database = flask_sqlalchemy.SQLAlchemy(main_website)
with open ("secretKey.txt") as secret_key_text:
    main_website.secret_key = secret_key_text.read()

# Form order class
class FormOrders(main_database.Model):
    # Setup
    id = main_database.Column(main_database.Integer, primary_key = True)
    name = main_database.Column(main_database.String(20), nullable = False)
    content = main_database.Column(main_database.PickleType, nullable = False)
    dateCreated = main_database.Column(main_database.DateTime, default = datetime.datetime.utcnow)

# Get diamonds to stacks
def get_diamonds_to_stacks(amount_of_diamonds):
    order_cost = f"{int(amount_of_diamonds / 64)} stacks {amount_of_diamonds % 64} diamonds"
    return order_cost

# Error handling ==================================================================================

# Page not found
@main_website.errorhandler(404)
def page_not_found(error):
    return flask.render_template("pageNotFound.html"), 404

# Internal server error
@main_website.errorhandler(500)
def internal_server_error(error):
    return flask.render_template("internalServerError.html"), 500


# Pages ===========================================================================================

# Index page
@main_website.route("/")
def index():
    return flask.render_template("index.html")

# Blank page
@main_website.route("/blank")
def blank():
    return flask.render_template("blank.html")

# List of enchants page 
@main_website.route("/allEnchantments")
def all_enchants():
    return flask.render_template("allEnchantments.html", enchantDictionary = enchant_dictionary)

# Form related pages ==============================================================================

# Form and submissions
@main_website.route("/form", methods = ["POST", "GET"])
def form():
    # Clicked button
    if flask.request.method == "POST":
        # If submitting
        if flask.request.form["action"] == "Submit order!":
            # Get all data
            order_content = flask.request.form
            order_username = flask.request.form["Username"]

            # Make data look pretty
            order_content_dict = {}
            order_content_dict["Extra"] = {}
            ordered_products = []

            # Get all products
            for product_name in product_dictionary.keys():
                # Iterate through each field in order content
                for order_attribute in order_content.items():
                    # Get value for field
                    value_for_attribute = order_attribute[1]

                    # If the name is in the current field
                    if product_name in order_attribute[0]:
                        # Make it show just enchantment and enchant number
                        order_product = product_name
                        for character in order_attribute[0]:
                            if character.isnumeric():
                                order_product += f" {character}"
                                break

                        # Initialize the product if it hasn't been
                        if order_product not in ordered_products:
                            order_content_dict[order_product] = {}
                            ordered_products.append(order_product)
                            enchant_list = []

                        attribute = order_attribute[0].replace(order_product, "")

                        if "Multiple Choice" in attribute:
                            attribute = value_for_attribute

                        if (not "Name" in attribute) and (not "Additional" in attribute):
                            enchant_list.append(attribute[1::]) if attribute.startswith(" ") else enchant_list.append(attribute)
                            order_content_dict[order_product]["Enchantments"] = enchant_list

                        else:
                            order_content_dict[order_product][attribute] = value_for_attribute

            # Additional information
            order_content_dict["Extra"]["Additional Information"] = order_content["Additional Information"]
            # Minecraft server
            order_content_dict["Extra"]["Minecraft Server"] = order_content["Minecraft Server"]

            # Product cost
            order_price = 5

            # Get the product name (from "Sword 1" to "Sword")
            for product_ordered in ordered_products:
                product_ordered = product_ordered.replace(" ", "")
                for character in product_ordered:
                    if character.isnumeric():
                        product_ordered = product_ordered.strip(character)

                order_price += product_dictionary[product_ordered]["productCost"]

            order_content_dict["Extra"]["Estimated Cost"] = get_diamonds_to_stacks(order_price)

            # Submit
            form_submission = FormOrders(content = order_content_dict, name = order_username)

            # Save to database
            try:
                main_database.session.add(form_submission)
                main_database.session.commit()

            # Error happened
            except:
                flask.flash("There was a problem with submitting your order! Please contact Pink_Sheepy.")
                return flask.redirect("/")

            flask.flash(f"Your order (#{form_submission.id}) has been recieved!")
            flask.flash(f"Your estimated total cost is {get_diamonds_to_stacks(order_price)}. Please go to Sheepy's base to drop off payment.")
            return flask.redirect("/")

        # Still on first page
        else:
            order_content = {}
            for product in product_dictionary.items():
                order_content[product[0]] = int(flask.request.form[product[1]["variableName"]])

            # Going to next page
            if flask.request.form["action"] == "Next page":
                return flask.render_template("formEnchants.html", orderContent = order_content, productDictionary = product_dictionary)

            # Just getting price
            elif flask.request.form["action"] == "Estimated cost":
                order_cost = 5

                for ordered_product in order_content.items():
                    order_cost += int(ordered_product[1]) * int(product_dictionary[ordered_product[0]]["productCost"])

                flask.flash(f"Estimated total cost is {get_diamonds_to_stacks(order_cost)}.")
                return flask.redirect("/blank")

    # Not submitting
    else:
        order = FormOrders.query.order_by(FormOrders.dateCreated).all()
        return flask.render_template("formSelection.html", productDictionary = product_dictionary, order = order)

# View submissions
@main_website.route("/viewAllOrders")
def view_all_orders():
    all_orders = FormOrders.query.order_by(FormOrders.dateCreated).all()
    return flask.render_template("viewSubmissions.html", allOrders = all_orders, timedelta = datetime.timedelta)

# View order
@main_website.route("/viewOrder/<int:id>")
def view_order(id):
    order = FormOrders.query.filter_by(id = id).first()

    # Make sure the order is valid
    if order is not None:
        return flask.render_template("orderViewGUI.html", order = order, timedelta = datetime.timedelta, product_dictionary = product_dictionary)

    # Order is not valid
    else:
        flask.flash(f"Order ID {id} is not valid.")
        return flask.redirect("/viewAllOrders")

# Delete submission enter password
@main_website.route("/removeOrder/<int:id>")
def remove_order_password_enter(id):
    order = FormOrders.query.filter_by(id = id).first()

    # Make sure the order is valid
    if order is not None:
        return flask.render_template("removeSubmission.html", orderID = id, order = order)

    # Order is not valid
    else:
        flask.flash(f"Order ID {id} is not valid.")
        return flask.redirect("/viewAllOrders")

# Delete submission
@main_website.route("/deleteOrder/<int:id>", methods = ["POST", "GET"])
def delete_order(id):
    # If removing
    if flask.request.method == "POST":
        order_to_delete = FormOrders.query.get_or_404(id)

        # Check password
        password_inputted = flask.request.form["PasswordRemove"]

        # Easter egg
        if password_inputted == "LaCraftyIsSmelly!@#$":
            flask.flash("Your password is the truth.")

        with open ("password.txt") as real_password_text:
            # Password matches
            if password_inputted == real_password_text.read():
                # Attempt to remove
                try:
                    main_database.session.delete(order_to_delete)
                    main_database.session.commit()
                    flask.flash(f"Successfully deleted order {id}")

                # Failed to remove
                except:
                    flask.flash(f"There was a problem removing order {id}")

                return flask.redirect("/viewAllOrders")

            # Password doesn't match
            else:
                flask.flash(f"Password {password_inputted} is not correct. Nice try.")

    return flask.redirect(f"/removeOrder/{id}")

# Run website =====================================================================================
if __name__ == "__main__":
    main_website.run(debug = True)
    # main_website.run(debug = False)
    # main_website.run(host = "0.0.0.0", port = 5001)