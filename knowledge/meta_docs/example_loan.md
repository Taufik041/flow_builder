# example_loan

Source: https://developers.facebook.com/documentation/business-messaging/whatsapp/flows/gettingstarted/pre-approved-loan

## Use Case Guide: Get leads for a pre-approved loan / credit card

Updated: Feb 26, 2026

## Intro and Overview

WhatsApp is changing the way people access financial services, offering a convenient and immediate solution for urgent financial needs. However, the back and forth messaging, and lack of structured guidance leaves some users feeling uncertain and results in them dropping off in the middle of the journey.
WhatsApp Flows enables a pre-approved loan experience that makes the borrowing process easier to follow and quicker to complete, allowing users to secure funds with just a few clicks.
In this guide, we will walk through the entire process to build a Flow for a ‘Pre-approved loan’ use case. The templates here can be adapted to suit your use case.
Flows we will build will demonstrate how you can:
Resent user-specific options, which can then be customised by a user
Build user selections and input fields to collect data from a user
Create a mechanism to confirm the user’s identity, in this case by asking for their date of birth (could be by uploading a photo or a document etc.).
Confirm the Flow has been completed, both in the Flow and with a follow up message.
Publish, Send, and Monitor your Flow
This template can be further adapted to add additional security measures (e.g. OTP) or collect additional information from the customer. We’ve created the Flow JSON Template for a full loan application journey with KYC and suitability checks that you can view here.

## Getting Started

To follow this guide, ensure you have:
Completed prerequisites for building Flows.
A Glitch⁠ account

## Flows JSON Template

Flow JSON
{
  "version": "7.3",
  "data_api_version": "3.0",
  "routing_model": {
    "LOAN": [
      "DETAILS"
    ],
    "DETAILS": [
      "SUMMARY"
    ],
    "SUMMARY": [
      "COMPLETE"
    ],
    "COMPLETE": []
  },
  "screens": [
    {
      "id": "LOAN",
      "title": "Your pre-approved loan",
      "data": {
        "tenure": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {
                "type": "string"
              },
              "title": {
                "type": "string"
              }
            }
          },
          "__example__": [
            {
              "id": "months12",
              "title": "12 months"
            },
            {
              "id": "months24",
              "title": "24 months"
            },
            {
              "id": "months36",

## Here is your pre-approved loan

Here is an offer exclusively made for you. Claim it as it is or tweak it as per your needs.

## Loan amount

Loan amount

## ₹ 7,20,000

₹ 7,20,000

## Tenure

Tenure

## 48 months

48 months
Estimated EMI
₹ 18,000
Interest rate
9% pa
Continue

### Create new flow from a template

In the Flows section of WhatsApp Manager⁠ click on the Create Flow button in the top right corner.
In the Create page, fill in the details for the pre-approved loan Flow:
Name - Type Pre-Approved Loan, or choose another name you like.
Categories - Select Lead generation.
Template - Choose Pre-Approved Loan. You can further customize the template to suit your use case.
Click Create to create Flow.
You can preview the Flow on the right of the Builder UI.
The Flow remains in the draft state as you edit it. You can share it with your team for testing purposes only. To share it with a large audience, you’ll need to publish it. However, you can’t edit the Flow once you publish. Since you will still need to add the endpoint URL for this Flow, leave it as a draft for now and proceed to the next step, where you’ll configure the demo backend endpoint.
See also
Flow JSON Overview

## Configure Demo Backend on Glitch

WhatsApp Flows lets you connect to an external endpoint. This endpoint can provide dynamic data for your Flow and control routing. It also receives user-submitted responses from the Flow.
For testing purposes, this template uses Glitch to host the endpoint. Using Glitch is entirely optional, and not required to use Flows. You can clone the endpoint code from GitHub⁠ and run it in any environment you prefer.

### 1. Remix (fork) Glitch endpoint

Access the endpoint code in Glitch⁠ and remix it to get your unique domain. To remix it, click Remix at the top of the page. A unique domain will appear as a placeholder in the input element on the right side of the Glitch page.

### 2. Setup encryption key

Private key helps decrypt the messages received. The passphrase will be used to verify the private key. Along with the private key, you also need its corresponding public key, which you’ll upload later. Never use the private keys for your production accounts here. Create a temporary private key for testing on Glitch, and then replace it with your production key in your own infrastructure.
Generate the public-private key pair by running the command below in the Glitch terminal. Replace YOUR_PASSPHRASE with your designated passphrase. Access the Glitch terminal by clicking the TERMINAL tab at the bottom of the page a run following command: node src/keyGenerator.js YOUR_PASSPHRASE
Copy the passphrase and private key and paste them to the .env file (Make sure to add quotes around values). Click on the file labeled .env on the left sidebar, then click on ✏️ Plain text on top. Do not edit it directly from the UI, as it will break your key formatting.
After you set the environment variables, copy the public key that you generated and upload the public key via the Graph API.

### 3. Set endpoint URI

Once you set up encryption keys, you can proceed with setting Endpoint URI for your flow.
At the top right of the Glitch page, click on Share and copy the Live Site URL from the displayed modal.
Head to the Flow Builder⁠ and in the Flow Builder click on the three dot menu in top right corner of the screen. Select Setup under the Endpoint section.
A popup will appear, allowing you to configure the endpoint URI, business phone number, and app on Meta for Developers. Save the Live Site URL copied from the Glitch into the first step of modal.
After making the necessary configurations, perform a health check from the last step of the modal. You should be able to get a successful response (if you get an error please check the details and the provided resolution advice).

### 4. Set App Secret (optional)

App secret is used in signature verification. It helps you check whether a request is coming via WhatsApp and, therefore, is safe to process. You’ll add it to the .env file.
To access your app secret, select your App from the dashboard in the Meta for Developers. In the left navigation pane under App settings, choose Basic. Click Show under App secret and copy the secret. Then, return to Glitch, open the .env file, and create a variable named APP_SECRET with the value of the secret you copied.
Now you have completed all the required steps to be able to test flow with the provided endpoint.
See also
Detailed code walk through for demo backend
Implementing endpoint for Flows for full details on how to build production endpoint

## Testing and Debugging

### Debug flow using the interactive preview

After you complete the configurations, toggle the interactive preview in the WhatsApp Builder UI to test the Flow.
Trigger the interactive preview by clicking on settings menu in the Preview section of the Flow Builder and enabling Interactive mode toggle.
In the modal that appears, select the phone number, enter any string as Flow token and choose the Request data option under Request data on the first screen. This sends a request to the endpoint to retrieve data for the first screen.
Now, click on Actions tab at the bottom of the code editor in Builder. You’ll see an init action in the list. Click on it to see the details and you will see the decrypted request sent to the endpoint. There will also be decrypted response received from endpoint with the initial data payload.
Return back to Preview and proceed to change tenure by selecting an option from the Tenure dropdown. Back in Actions tab notice how the tenure is set to selected new tenure and the action has changed to data_exchange.
Keep testing out the Flow and observe the data changes in the Actions tab. Similar logs will be generated when users interact with the Flow from their mobile devices.
You can also see decrypted request and responses logged in the Glitch LOGS tab at the bottom of the Glitch screen.

### Send draft flow to your device

Before you publish your flow you can also send it and test it on an actual device. To send draft flow to your device, follow instructions here.
See also
Flow Testing and debugging guide

## Publishing

When you first created your Flow, it entered the Draft state. And as you edited and saved the modified Flow JSON content, it remained in the Draft state. You are able to send the Flow while it’s in the Draft state, but only for testing purposes. If you want to send the Flow to a larger audience, you’ll need to Publish the Flow.
You can publish your Flow once you have ensured that:
All validation errors and publishing checks have been resolved.
The Flow meets the design principles of WhatsApp Flows
The Flow complies with WhatsApp Terms of Service⁠, the WhatsApp Business Messaging Policy⁠ and, if applicable, the WhatsApp Commerce Policy⁠
Remember, once a Flow has been published it can no longer be modified. See Flow Status Lifecycle for more information on the different Flow states.
To publish your Flow, open the three dot menu to the right of the Save button and click Publish. Once published, the Flow can be sent to anyone!

## Sending

You can send your WhatsApp Flow as:
Template messages - these do not require a 24-hour customer service window to be open between you and the message recipient before the message can be sent.
Interactive Flow messages - these can only be sent to a user when a customer service window is open between you and the user.
Learn more about sending your Flow

## Receiving flow response

Upon flow completion a response message will be sent to the WhatsApp chat. You will receive it in the same way as you receive all other messages from the user - via message webhook.
Learn more about how to setup messaging webhook

## Monitoring

Flow monitoring is only applicable to Flows with endpoint.
After your Flow is published and being sent to the customers, it is important to monitor your Flow’s health and address any problems as they are discovered by WhatsApp.
There are multiple ways how you can monitor your flows:
Metrics Dashboard in WhatsApp Account Manager
Navigate to Flow section of WhatsApp Account Manager⁠ and click on any published flow with the endpoint. You will be presented with a Details page with a Performance Metrics Dashboard.
Metrics API
All the data presented in the Details page is also available to be queried through Flows Metrics API.
Quality Webhooks
You should also subscribe to Flows Quality Webhooks to be updated in real time about the statuses and performance of your business’ Flows.
See Flow Health and Monitoring overview for more information.

## Next Steps

Now that you have successfully completed this guide, learn more about what you can do with this Flows in our Guides and Reference sections.

## Overview of demo backend

There are four JavaScript files in the Glitch example src directory⁠: encryption.js, flow.js, keyGenerator.js, and server.js. The entry file is server.js, so let’s look at it first.

### server.js

The server.js file starts by configuring the Express application to use the express.json middleware to parse incoming JSON requests. Then, it loads the environment variables needed for the endpoint.

```
const { APP_SECRET, PRIVATE_KEY, PASSPHRASE, PORT = "3000" } = process.env;
```

The server.js file also contains a POST endpoint that performs different steps:
Checks that the private key is present:

```
if (!PRIVATE_KEY) {
  throw new Error('Private key is empty. Please check your env variable "PRIVATE_KEY".');
}
```

Validates the request signature using the isRequestSignatureValid function found at the bottom of the file:

```
if(!isRequestSignatureValid(req)) {
// Return status code 432 if request signature does not match.
// To learn more about return error codes visit: /documentation/business-messaging/whatsapp/flows/reference/error-codes#endpoint_error_codes
  return res.status(432).send();
}
```

Decrypts incoming messages using the decryptRequest function found in the encryption.js file:

```
let decryptedRequest = null;
try {
  decryptedRequest = decryptRequest(req.body, PRIVATE_KEY, PASSPHRASE);
} catch (err) {
  console.error(err);
  if (err instanceof FlowEndpointException) {
    return res.status(err.statusCode).send();
  }
  return res.status(500).send();
}

const { aesKeyBuffer, initialVectorBuffer, decryptedBody } = decryptedRequest;
console.log("💬 Decrypted Request:", decryptedBody);
```

Decides what Flow screen to display to the user. You’ll look at the getNextScreen function in detail later.

```
const screenResponse = await getNextScreen(decryptedBody);
console.log("👉 Response to Encrypt:", screenResponse);
```

Encrypts the response to be sent to the user:

```
res.send(encryptResponse(screenResponse, aesKeyBuffer, initialVectorBuffer));
```

### encryption.js

This file contains the logic for encrypting and decrypting messages exchanged for security purposes. See Code examples section of Endpoint implementation guide for encryption examples in other languages.

### keyGenerator.js

This file helps generate the private and public keys, as you saw earlier.

### flow.js

The logic for handling the Flow is housed in this file. It starts with an object assigned the name SCREEN_RESPONSES. The object contains screen IDs with their corresponding details, such as the preset data used in the data exchanges. This object is generated from Flow Builder under “...” > Endpoint > Snippets > Responses. In the same object, you also have another ID, SUCCESS, that is sent back to the client device when the Flow is successfully completed. This closes the Flow.
The LOAN_OPTIONS object is an example configuration for monthly repayments for various amounts and tenures.
The getNextScreen function contains the logic that guides the endpoint on what Flow data to display to the user. It starts by extracting the necessary data from the decrypted message.

```
const { screen, data, version, action, flow_token } = decryptedBody;
```

WhatsApp Flows endpoints usually receive three types of requests:
A data_exchange request signified by a data_exchange action
An error notification request signified by a data.error element
A health check request signified by a ping action

### Health check and Error handler

The function handles the health check and error notifications using if statements and responds accordingly, as shown in the snippet below:

```
// handle health check request
if (action === "ping") {
    return {
        version,
        data: {
            status: "active",
        },
    };
}

// handle error notification
if (data?.error) {
    console.warn("Received client error:", data);
    return {
        version,
        data: {
            acknowledged: true,
        },
    };
}
```

### INIT handler

When a user clicks the Flow’s call to action (CTA) button, a request with INIT action is sent to the endpoint. This action returns the initial loan data and pre-sets the dropdowns on the LOAN screen.

```
// handle initial request when opening the flow and display LOAN screen
if (action === "INIT") {
  return {
    ...SCREEN_RESPONSES.LOAN,
  };
}
```

### data-exchange handlers

For data_exchange actions, a switch case structure is used to determine what data to send back based on the screen ID and other request data.
For the first screen with ID LOAN we handle two requests. If the emi field of the request is null, it means that the user has selected a new tenure or amount dropdown option and therefore a new emi option is returned back to the client to update the screen with a new monthly payment.
If the emi field of request is specified, it means that the user clicked on the Continue button on the Loan screen. We return the next screen name in the response (DETAILS) with selected amount, tenure and emi. We also set initial values from SCREEN_RESPONSES.DETAILS.data for is_upi and is_account (initially both are set to false, so no payment option is rendered initially).
For handling of DETAILS screen, if we receive request with non-null payment_mode, we return default SCREEN_RESPONSES.DETAILS.data with is_upi and is_account set as per user inputs.

```
// Handles user selecting UPI or Banking selector
if (data.payment_mode != null) {
  return {
    ...SCREEN_RESPONSES.DETAILS,
    data: {
      is_upi: data.payment_mode == "UPI",
      is_account: data.payment_mode == "Bank",
    },
  };
}
```

For instance, the UPI ID input field in UI is enabled only when the user selects the UPI option. The enabling and disabling of the fields are handled when a data_exchange request is received.
If the payment_mode property is null in the request it means that user has clicked on Continue button and as data for SUMMARY screen we return default SUMMARY screen data with overridden amount, tenure and emi (which are all copied over from request payload) and we add formatted payment_mode. In the production endpoint you would want to store the payment details at this point.

```
return {
  ...SCREEN_RESPONSES.SUMMARY,
  data: {
    // copy initial screen data then override specific fields
    ...SCREEN_RESPONSES.SUMMARY.data,
    amount: data.amount,
    tenure: data.tenure,
    emi: data.emi,
    payment_mode: "Transfer to " + payment_string,
  },
};
```

After the SUMMARY screen is submitted from the client, a success response is sent to the client device to mark the Flow as complete.
Did you find this page helpful?