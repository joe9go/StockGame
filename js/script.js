// store all predictions that user made
let predictions = [];

const url = 'http://724a-2607-b400-a4-2e30-51b1-3362-821b-7dfd.ngrok.io'

const submitPrediction = (event)=>{
    let prediction = {
        tick: document.getElementById('tick').value,        
        price: document.getElementById('price').value,
        date: document.getElementById('dt').value
    }
    predictions.push(prediction);

    // reset entry values
    document.getElementById('tick').value = "";
    document.getElementById('price').value = 0;
    document.getElementById('dt').value = "";

    // show the data we've just added
    let data = JSON.stringify(prediction)
    console.log(data)

    // POST request
}

// event for submit button
document.addEventListener('DOMContentLoaded', ()=>{
    document.getElementById('submit').addEventListener('click', submitPrediction);
});
