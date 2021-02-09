var selectSongs = document.getElementById("selectSongs");
var contents;

for (let i = 1; i <= 50; i++) {
  contents += "<option>" + i + "</option>";
}

selectSongs.innerHTML = contents;