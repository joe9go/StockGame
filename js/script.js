// store all predictions that user made
let predictions = [];

const url = 'http://724a-2607-b400-a4-2e30-51b1-3362-821b-7dfd.ngrok.io'

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

const submitPrediction = (event)=>{
    let prediction = {
        company: document.getElementById('tick').value,        
        value: document.getElementById('price').value,
        date: document.getElementById('dt').value,
        user: getCookie("username"),
        user_token: getCookie("token")
    }
    predictions.push(prediction);

    // reset entry values
    document.getElementById('tick').value = "";
    document.getElementById('price').value = 0;
    document.getElementById('dt').value = "";

    // show the data we've just added
    let data = JSON.stringify(prediction)
    

    // POST request
    submit(data)
}

// event for submit button
document.addEventListener('DOMContentLoaded', ()=>{
    document.getElementById('submit').addEventListener('click', submitPrediction);
});

if (getCookie("username") != undefined){
    document.getElementById('login').text=getCookie("username");
}

async function submit(data){
    console.log(data)
    await fetch(url,
    {'method':'POST',"headers":{'request':'prediction'},
    "body":data})
    .then(response => response.json())
    .then(data => {console.log(data)})
}