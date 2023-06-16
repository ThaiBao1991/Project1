/* TRUNCATE CARD TITLE */
window.addEventListener("load",function(){
    truncateCardTitle();
})

function truncateCardTitle(){
    var cardList = document.getElementsByClassName("card-title");
    console.log(cardList);
    for(var i=0;i<cardList.length;i++){
        var text= cardList[i].innerHTML;
        var newtext = truncateString(text,40);
        cardList[i].innerHTML = newtext;
    }
}

function truncateString(str,num){
    if(str.length >num){
        return str.slice(0,num) + "...";
    }else{
        return str;
    }
}

/* Sidebar mini */
var toggleBtn = document.querySelector('.sidebarMini__button');
var sidebarMini = document.querySelector('.sidebarMini');
var switchBtn = document.querySelector('#checkbox');

toggleBtn.addEventListener('click',function(){
    sidebarMini.classList.toggle('is-opened');
})

switchBtn.addEventListener('click',function(){
    document.querySelector('body').classList.toggle('darkMode');
})