// store all predictions that user made
let userinformation = [];

const url = 'http://724a-2607-b400-a4-2e30-51b1-3362-821b-7dfd.ngrok.io'

const register = (event)=>{
    let userinfo = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
    }
    userinformation.push(userinfo);

    // reset entry values
    document.getElementById('username').value = "";
    document.getElementById('password').value = "";

    // show the data we've just added
    let data = JSON.stringify(userinfo)
    console.log(data)

    // POST request
    submit(data)
}

// event for submit button
document.addEventListener('DOMContentLoaded', ()=>{
    document.getElementById('login-button').addEventListener('click', register);
});

async function submit(data){
    const response = await fetch(url,
    {'method':'POST',"headers":{'request':'register'},
    "body":data})
    .then(response => response.json())
    .then(data => console.log(data)).catch(()=>{
        console.log("unable to register")
    })
}