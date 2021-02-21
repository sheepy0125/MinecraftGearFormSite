# Setup ===========================================================================================

# Import
import flask
import flask_sqlalchemy
import datetime
from productDictionary import *

# Setup website
mainWebsite = flask.Flask(__name__, template_folder = "template")
mainWebsite.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ordering.db"
mainDB = flask_sqlalchemy.SQLAlchemy(mainWebsite)
with open ("secretKey.txt") as secretKeyText:
    mainWebsite.secret_key = secretKeyText.read()

# Form order class
class FormOrders(mainDB.Model):
    # Setup
    id = mainDB.Column(mainDB.Integer, primary_key = True)
    name = mainDB.Column(mainDB.String(20), nullable = False)
    content = mainDB.Column(mainDB.PickleType, nullable = False)
    dateCreated = mainDB.Column(mainDB.DateTime, default = datetime.datetime.utcnow)

# Get diamonds to stacks
def getDiamondsToStacks(amountOfDiamonds):
    orderCost = f"{int(amountOfDiamonds / 64)} stacks {amountOfDiamonds % 64} diamonds"
    return orderCost

# Error handling ==================================================================================

# Page not found
@mainWebsite.errorhandler(404)
def pageNotFoundError(error):
    return flask.render_template("pageNotFound.html"), 404

# Internal server error
@mainWebsite.errorhandler(500)
def internalServerError(error):
    return flask.render_template("internalServerError.html"), 500


# Pages ===========================================================================================

# Index page
@mainWebsite.route("/")
def index():
    return flask.render_template("index.html")

# Blank page
@mainWebsite.route("/blank")
def blank():
    return flask.render_template("blank.html")

# List of enchants page 
@mainWebsite.route("/allEnchantments")
def allEnchants():
    return flask.render_template("allEnchantments.html", enchantDictionary = enchantDictionary)

# Form related pages ==============================================================================

# Form and submissions
@mainWebsite.route("/form", methods = ["POST", "GET"])
def form():
    # Clicked button
    if flask.request.method == "POST":
        # If submitting
        if flask.request.form["action"] == "Submit order!":
            # Get all data
            orderContent = flask.request.form
            orderUsername = flask.request.form["Username"]

            # Make data look pretty
            orderContentDict = {}
            orderContentDict["Extra"] = {}
            orderedProducts = []

            # Get all products
            for productName in productDictionary.keys():
                # Iterate through each field in order content
                for orderAttribute in orderContent.items():
                    # Get value for field
                    valueForAttribute = orderAttribute[1]

                    # If the name is in the current field
                    if productName in orderAttribute[0]:
                        # Make it show just enchantment and enchant number
                        orderProduct = productName
                        for character in orderAttribute[0]:
                            if character.isnumeric():
                                orderProduct += f" {character}"
                                break

                        # Initialize the product if it hasn't been
                        if orderProduct not in orderedProducts:
                            orderContentDict[orderProduct] = {}
                            orderedProducts.append(orderProduct)
                            enchantList = []

                        attribute = orderAttribute[0].replace(orderProduct, "")

                        if "Multiple Choice" in attribute:
                            attribute = valueForAttribute

                        if (not "Name" in attribute) and (not "Additional" in attribute):
                            enchantList.append(attribute[1::]) if attribute.startswith(" ") else enchantList.append(attribute)
                            orderContentDict[orderProduct]["Enchantments"] = enchantList

                        else:
                            orderContentDict[orderProduct][attribute] = valueForAttribute

            # Additional information
            orderContentDict["Extra"]["Additional Information"] = orderContent["Additional Information"]
            # Minecraft server
            orderContentDict["Extra"]["Minecraft Server"] = orderContent["Minecraft Server"]

            # Product cost
            orderPrice = 5

            # Get the product name (from "Sword 1" to "Sword")
            for productOrdered in orderedProducts:
                productOrdered = productOrdered.replace(" ", "")
                for character in productOrdered:
                    if character.isnumeric():
                        productOrdered = productOrdered.strip(character)

                orderPrice += productDictionary[productOrdered]["productCost"]

            orderContentDict["Extra"]["Estimated Cost"] = getDiamondsToStacks(orderPrice)

            # Submit
            formSubmission = FormOrders(content = orderContentDict, name = orderUsername)

            # Save to database
            try:
                mainDB.session.add(formSubmission)
                mainDB.session.commit()

            # Error happened
            except:
                flask.flash("There was a problem with submitting your order! Please contact Pink_Sheepy.")
                return flask.redirect("/")

            flask.flash(f"Your order (#{formSubmission.id}) has been recieved!")
            flask.flash(f"Your estimated total cost is {getDiamondsToStacks(orderPrice)}. Please go to Sheepy's base to drop off payment.")
            return flask.redirect("/")

        # Still on first page
        else:
            orderContent = {}
            for product in productDictionary.items():
                orderContent[product[0]] = int(flask.request.form[product[1]["variableName"]])

            # Going to next page
            if flask.request.form["action"] == "Next page":
                return flask.render_template("formEnchants.html", orderContent = orderContent, productDictionary = productDictionary)

            # Just getting price
            elif flask.request.form["action"] == "Estimated cost":
                orderCost = 5

                for orderedProduct in orderContent.items():
                    orderCost += int(orderedProduct[1]) * int(productDictionary[orderedProduct[0]]["productCost"])

                flask.flash(f"Estimated total cost is {getDiamondsToStacks(orderCost)}.")
                return flask.redirect("/blank")

    # Not submitting
    else:
        order = FormOrders.query.order_by(FormOrders.dateCreated).all()
        return flask.render_template("formSelection.html", productDictionary = productDictionary, order = order)

# View submissions
@mainWebsite.route("/viewAllOrders")
def viewAllOrders():
    allOrders = FormOrders.query.order_by(FormOrders.dateCreated).all()
    return flask.render_template("viewSubmissions.html", allOrders = allOrders)

# View order
@mainWebsite.route("/viewOrder/<int:id>")
def orderView(id):
    order = FormOrders.query.filter_by(id = id).first()

    # Make sure the order is valid
    if order is not None:
        return flask.render_template("orderView.html", order = order)

    # Order is not valid
    else:
        flask.flash(f"Order ID {id} is not valid.")
        return flask.redirect("/viewAllOrders")

# Delete submission enter password
@mainWebsite.route("/removeOrder/<int:id>")
def removeSubmissionEnterPassword(id):
    order = FormOrders.query.filter_by(id = id).first()

    # Make sure the order is valid
    if order is not None:
        return flask.render_template("removeSubmission.html", orderID = id, order = order)

    # Order is not valid
    else:
        flask.flash(f"Order ID {id} is not valid.")
        return flask.redirect("/viewAllOrders")

# Delete submission
@mainWebsite.route("/deleteOrder/<int:id>", methods = ["POST", "GET"])
def deleteSubmission(id):
    # If removing
    if flask.request.method == "POST":
        orderToDelete = FormOrders.query.get_or_404(id)

        # Check password
        passwordInputted = flask.request.form["PasswordRemove"]

        # Easter egg
        if passwordInputted == "LaCraftyIsSmelly!@#$":
            flask.flash("Your password is the truth.")

        with open ("password.txt") as realPasswordText:
            # Password matches
            if passwordInputted == realPasswordText.read():
                # Attempt to remove
                try:
                    mainDB.session.delete(orderToDelete)
                    mainDB.session.commit()
                    flask.flash(f"Successfully deleted order {id}")

                # Failed to remove
                except:
                    flask.flash(f"There was a problem removing order {id}")

                return flask.redirect("/viewAllOrders")

            # Password doesn't match
            else:
                flask.flash(f"Password {passwordInputted} is not correct. Nice try.")

    return flask.redirect(f"/removeOrder/{id}")

# Run website =====================================================================================
if __name__ == "__main__":
    # mainWebsite.run(debug = True)
    mainWebsite.run(debug = False)
    # mainWebsite.run(host = "0.0.0.0", port = 5001)