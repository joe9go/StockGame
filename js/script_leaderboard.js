// store all predictions that user made
let userinformation = [];

const url = 'http://724a-2607-b400-a4-2e30-51b1-3362-821b-7dfd.ngrok.io'

var leaders;

async function getLeaderboard(data){
    await fetch(url,
    {'method':'POST',"headers":{'request':'leaderboard'},
    "body":JSON.stringify(data)})
    .then(response => response.json())
    .then(data => {leaders = data})
    board = document.getElementById("leaderboard");
    for(const score of leaders.scores){
        newRow = board.insertRow()
        newCell = newRow.insertCell();
        newCell.textContent = score[0]
        newCell = newRow.insertCell();
        newCell.textContent = score[1]
    }
}

getLeaderboard({});

