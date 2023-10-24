// you may uncomment this and the buy and sell pages will display stocks, that match your input, as you are typing
// youo must uncomment sections from the buy and sell templates aswell for this feature to be enabled

// let input = document.getElementById('symbol');
// input.addEventListener('input', async function() {
//     let response = await fetch('/search?symbol=' + input.value);
//     if (response == 1) {
//         document.getElementById('ticker').innerHTML = "helelo";
//         document.getElementById('name').innerHTML = "hi";
//         document.getElementById('price').innerHTML = "hi";
//         return;
//     }

//     let stock_data = await response.json();

//     document.getElementById('ticker').innerHTML = stock_data["symbol"];
//     document.getElementById('name').innerHTML = stock_data["name"];
//     document.getElementById('price').innerHTML = stock_data["price"];
// });