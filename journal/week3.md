# Week 3 — Decentralized Authentication

## AWS Cognito
In this live session, we first created a UserPool in AWS Cognito.

**Steps to setup UserPool in AWS Cognito**
- Login to your AWS Console
- Check your region in which you want to use your service. I personally prefer `us-east-1` region as in that region most of the services works well.
- Search for **Cognito** service and you will find **UserPool** tab in your left side panel.
- After clicking on **UserPool** -> **Create UserPool**.
- You will be displayed with a **Authentication providers** page where I chose **Username** and **Email** for Cognito user pool sign-in options -> click **Next**
- Password Policy I kept it as **Cognito Default**.
- Under Multi-factor authentication -> I selected **No MFA** -> **Next**
- In User account recovery -> checkbox **Email only** -> **Next**
- Under Required attributes -> I selected **Name** and **preferred username** -> **Next**
- Then I chose **Send email with Cognito** for first time -> **Next**
- After that you will be asked to give your User Pool Name , I gave it as **crddur-user-pool** -> under Initial app client I kept it as **Public client** -> enter app client name **(eg: cruddur)** -> **Next**
- You will get a chance to verify all the filled details and then click on **Create User Pool**, your userpool is being created.

## Gitpod Code Working 
Install AWS Amplify as it is a development platform and provides you a set of pre-built UI components and Libraries. 
```
cd front-react-js 
npm i aws-amplify --save
```
After installing this you will find the library `"aws-amplify": "<version>",` in the frontend-react-js directory's `package.json` file.

**Note: make sure you are running these commands in your `frontend-react-js` directory.**

### Configure Amplify
Add the code below in `app.js` of frontend-react-js directory.
```js
import { Amplify } from 'aws-amplify';

Amplify.configure({
  "AWS_PROJECT_REGION": process.env.REACT_AWS_PROJECT_REGION,
  "aws_cognito_identity_pool_id": process.env.REACT_APP_AWS_COGNITO_IDENTITY_POOL_ID,
  "aws_cognito_region": process.env.REACT_APP_AWS_COGNITO_REGION,
  "aws_user_pools_id": process.env.REACT_APP_AWS_USER_POOLS_ID,
  "aws_user_pools_web_client_id": process.env.REACT_APP_CLIENT_ID,
  "oauth": {},
  Auth: {
    // We are not using an Identity Pool
    // identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID, // REQUIRED - Amazon Cognito Identity Pool ID
    region: process.env.REACT_AWS_PROJECT_REGION,           // REQUIRED - Amazon Cognito Region
    userPoolId: process.env.REACT_APP_AWS_USER_POOLS_ID,         // OPTIONAL - Amazon Cognito User Pool ID
    userPoolWebClientId: process.env.REACT_APP_AWS_USER_POOLS_WEB_CLIENT_ID,   // OPTIONAL - Amazon Cognito Web Client ID (26-char alphanumeric string)
  }
});
```

Set the env vars below in docker-compose.yml:
```py
REACT_APP_AWS_PROJECT_REGION= "${AWS_DEFAULT_REGION}"
REACT_APP_AWS_COGNITO_REGION= "${AWS_DEFAULT_REGION}"
REACT_APP_AWS_USER_POOLS_ID= "us-east-1_XXXXXX"
REACT_APP_CLIENT_ID= "XXXXXX"
```

### Then to check the **Authentication Process** I added this code in my `HomeFeedPage.js`
```js
import { Auth } from 'aws-amplify';
```

delete the code with the cookies
```js
  const checkAuth = async () => {
    console.log('checkAuth')
    // [TODO] Authenication
    if (Cookies.get('user.logged_in')) {
        display_name: Cookies.get('user.name'),
        handle: Cookies.get('user.username')
    }
  };
```

```js
// set a state
const [user, setUser] = React.useState(null);

// check if we are authenicated
const checkAuth = async () => {
  Auth.currentAuthenticatedUser({
    // Optional, By default is false. 
    // If set to true, this call will send a 
    // request to Cognito to get the latest user data
    bypassCache: false 
  })
  .then((user) => {
    console.log('user',user);
    return Auth.currentAuthenticatedUser()
  }).then((cognito_user) => {
      setUser({
        display_name: cognito_user.attributes.name,
        handle: cognito_user.attributes.preferred_username
      })
  })
  .catch((err) => console.log(err));
};

// check when the page loads if we are authenicated
React.useEffect(()=>{
  loadData();
  checkAuth();
}, [])
```
### To render two React components: `DesktopNavigation` and `DesktopSidebar`, passing some properties to each of them.
```js
<DesktopNavigation user={user} active={'home'} setPopped={setPopped} />
<DesktopSidebar user={user} />
```
### Then added this code in `DesktopNavigation.js` which helps you to check whether you are logged in or not by passing the`user` to `ProfileInfo`.
```js
import './DesktopNavigation.css';
import {ReactComponent as Logo} from './svg/logo.svg';
import DesktopNavigationLink from '../components/DesktopNavigationLink';
import CrudButton from '../components/CrudButton';
import ProfileInfo from '../components/ProfileInfo';

export default function DesktopNavigation(props) {

  let button;
  let profile;
  let notificationsLink;
  let messagesLink;
  let profileLink;
  if (props.user) {
    button = <CrudButton setPopped={props.setPopped} />;
    profile = <ProfileInfo user={props.user} />;
    notificationsLink = <DesktopNavigationLink 
      url="/notifications" 
      name="Notifications" 
      handle="notifications" 
      active={props.active} />;
    messagesLink = <DesktopNavigationLink 
      url="/messages"
      name="Messages"
      handle="messages" 
      active={props.active} />
    profileLink = <DesktopNavigationLink 
      url="/@andrewbrown" 
      name="Profile"
      handle="profile"
      active={props.active} />
  }

  return (
    <nav>
      <Logo className='logo' />
      <DesktopNavigationLink url="/" 
        name="Home"
        handle="home"
        active={props.active} />
      {notificationsLink}
      {messagesLink}
      {profileLink}
      <DesktopNavigationLink url="/#" 
        name="More" 
        handle="more"
        active={props.active} />
      {button}
      {profile}
    </nav>
  );
}
```

### In `ProfileInfo.js`

This code defines a function called `signOut` that uses the `Auth` object from the `aws-amplify` library to sign out the currently authenticated user from an AWS Amplify application.
delete the following code:
```js
import Cookies from 'js-cookie'
```
Add the code below:
```js
import { Auth } from 'aws-amplify';
```
remove the following code
```js
    console.log('signOut')
    // [TODO] Authenication
    Cookies.remove('user.logged_in')
    //Cookies.remove('user.name')
    //Cookies.remove('user.username')
    //Cookies.remove('user.email')
    //Cookies.remove('user.password')
    //Cookies.remove('user.confirmation_code')
    window.location.href = "/"
```
Add the code below:
```js
const signOut = async () => {
  try {
      await Auth.signOut({ global: true });
      window.location.href = "/"
  } catch (error) {
      console.log('error signing out: ', error);
  }
}
```
Overall, this code provides a simple and straightforward way to sign out a user from an AWS Amplify application by using the `Auth` object from the `aws-amplify` library.

## Sign-in Page, Sign-out Page and Confirmation Page
### Implementation of the sign in page
From the **signinpage.js** remove the following code
```
import Cookies from 'js-cookie'

```

and replace with the following
```
import { Auth } from 'aws-amplify';
```

remove the following code 
```
  const onsubmit = async (event) => {
    event.preventDefault();
    setErrors('')
    console.log('onsubmit')
    if (Cookies.get('user.email') === email && Cookies.get('user.password') === password){
      Cookies.set('user.logged_in', true)
      window.location.href = "/"
    } else {
      setErrors("Email and password is incorrect or account doesn't exist")
    }
    return false
  }
```
and replace it with the new one
```
const onsubmit = async (event) => {
    setErrors('')
    event.preventDefault();
    Auth.signIn(email, password)
    .then(user => {
      console.log('user',user)
      localStorage.setItem("access_token", user.signInUserSession.accessToken.jwtToken)
      window.location.href = "/"
    })
    .catch(error => {
      if (error.code == 'UserNotConfirmedException') {
        window.location.href = "/confirm"
      }
      setErrors(error.message)
      });
    return false
  }
```

To try, just launch the container up on **"docker-compose.yml"**  and see if the login page works. to troubleshoot open "developer tools" or use inspect (browser) if you receive "NotAuthorizedException: Incorrect user or password".This means everything is set properly. if you got an error "auth not defined", the problem is the cognito user pool configuration. need to recreate.

Create a user on the cognito user pool and force change the password using the command on troubleshooting (there is no way to change on password via console). the password to login will be Testing1234! (as the commandline shows)

### Implementation the sign-up page
Since you have managed to access using the credential created via console, it is time to delete it cos it is no anymore needed.

From the **signuppage.js** remove the following code
```
import Cookies from 'js-cookie'

```

and replace with the following
```
import { Auth } from 'aws-amplify';
```

delete the following command
```
  const onsubmit = async (event) => {
    event.preventDefault();
    console.log('SignupPage.onsubmit')
    // [TODO] Authenication
    Cookies.set('user.name', name)
    Cookies.set('user.username', username)
    Cookies.set('user.email', email)
    Cookies.set('user.password', password)
    Cookies.set('user.confirmation_code',1234)
    window.location.href = `/confirm?email=${email}`
    return false
  }
```

and add the new code
```
const onsubmit = async (event) => {
    event.preventDefault();
    setErrors('')
    try {
      const { user } = await Auth.signUp({
        username: email,
        password: password,
        attributes: {
          name: name,
          email: email,
          preferred_username: username,
        },
        autoSignIn: { // optional - enables auto sign in after user is confirmed
          enabled: true,
        }
      }) ;
      console.log(user);
      window.location.href = `/confirm?email=${email}`
    } catch (error) {
        console.log(error);
        setErrors(error.message)
    }
    return false
  }
```

### Implementation of the confirmation page
from the confirmationpage.js, remove the following code

 ```
import Cookies from 'js-cookie'

```

and replace with the following
```
import { Auth } from 'aws-amplify';
```

and remove the following code
```
  const resend_code = async (event) => {
    console.log('resend_code')
    // [TODO] Authenication
  }
```
and replace with the following
``` 
const resend_code = async (event) => {
 
    setErrors('')
    try {
      await Auth.resendSignUp(email);
      console.log('code resent successfully');
      setCodeSent(true)
    } catch (err) {
      // does not return a code
      // does cognito always return english
      // for this to be an okay match?
      console.log(err)
      if (err.message == 'Username cannot be empty'){
        setCognitoErrors("You need to provide an email in order to send Resend Activiation Code")   
      } else if (err.message == "Username/client id combination not found."){
        setCognitoErrors("Email is invalid or cannot be found.")   
      }
    }
  }

```

and remove the following code
```
 const onsubmit = async (event) => {
    event.preventDefault();
    console.log('ConfirmationPage.onsubmit')
    // [TODO] Authenication
    if (Cookies.get('user.email') === undefined || Cookies.get('user.email') === '' || Cookies.get('user.email') === null){
      setErrors("You need to provide an email in order to send Resend Activiation Code")   
    } else {
      if (Cookies.get('user.email') === email){
        if (Cookies.get('user.confirmation_code') === code){
          Cookies.set('user.logged_in',true)
          window.location.href = "/"
        } else {
          setErrors("Code is not valid")
        }
      } else {
        setErrors("Email is invalid or cannot be found.")   
      }
    }
    return false
  }
```

and replace with the cognito code
```
const onsubmit = async (event) => {
  event.preventDefault();
  setCognitoErrors('')
  try {
    await Auth.confirmSignUp(email, code);
    window.location.href = "/"
  } catch (error) {
    setCognitoErrors(error.message)
  }
  return false
}
```

### Implementation of the recovery page
from the recoverpage.js, add the following code

 ```
import { Auth } from 'aws-amplify';
```

remove the following code
```
  const onsubmit_send_code = async (event) => {
    event.preventDefault();
    console.log('onsubmit_send_code')
    return false
  }
```

and add the these lines
```
const onsubmit_send_code = async (event) => {
    event.preventDefault();
    setErrors('')
    Auth.forgotPassword(username)
    .then((data) => setFormState('confirm_code') )
    .catch((err) => setErrors(err.message) );
    return false
  }
```

remove the following code
```
  const onsubmit_confirm_code = async (event) => {
    event.preventDefault();
    console.log('onsubmit_confirm_code')
    return false
  }
```

with the following new code
```
const onsubmit_confirm_code = async (event) => {
  event.preventDefault();
  setCognitoErrors('')
  if (password == passwordAgain){
    Auth.forgotPasswordSubmit(username, code, password)
    .then((data) => setFormState('success'))
    .catch((err) => setCognitoErrors(err.message) );
  } else {
    setCognitoErrors('Passwords do not match')
  }
  return false
}
```
#### Retrive submitted values across different pages in React.js

In our application, there are 2 user experience problems:
- During the confirmation, user needs to write the email manually. this could cause possible human error.
- After the registration, user gets redirected to the home page but not signed in yet. this could create confusion and user can create a new account accidentally.

The solution is to store the value using localstorage (many thanks to Abdassalam Hashnode) and use this across other pages.

The changes will be between the signuppage.js, confirmationpage.js and signinpage.js


From the signup page, add the following code this will store the email to the local storage
```
// SignupPage.js
const onsubmit = async (event) => {
// ...
    try {
// ...
// Store email in local storage to use it in confirmation & sign-in page
        localStorage.setItem('email', email);
// redirect user to confirmation page after signing up
        window.location.href = `/confirm`
    } 
// ...

```

from the confirmation page, add the following code. this checks if the local storage contains email

```
// ConfirmationPage.js
// ...
// Get email from the signup page where we stored the email in localStorage
React.useEffect(() => {
  const storedEmail = localStorage.getItem('email');
// check if the email is set, if it's not set then we will ignore it, and use the value typed in the email box:
  if (storedEmail) {
// Filling the Email
    setEmail(storedEmail);
  }
}, []);

const onsubmit = async (event) => {
// ...
```

for the signup page, add the following code. this gets the email from the local storage to the confirmation page:
```
// SigninPage.js
// Get email from the signup page where we stored the email in localStorage
React.useEffect(() => {
  const storedEmail = localStorage.getItem('email');
  if (storedEmail) {
    setEmail(storedEmail);
// Remove the email from local storage because we're done with it.
    localStorage.removeItem('email'); 
  }
}, []);
```

To redirect the home page already logged in, insert the following code
```
// ConfirmationPage.js
const onsubmit = async (event) => {
// ...
  try {
    await Auth.confirmSignUp(email, code);
// Redirect user to sign-in page instead of home page.
    window.location.href = "/signin"
// ...
}
```

# Troubleshooting

  #### Force password change for your cognito registered user: 

 ```python
  aws cognito-idp admin-set-user-password --username nameofusername --password Testing1234! --user-pool-id "${AWS_USER_POOLS_ID}" --permanent
```

