// Homepage Carousel
$(window).on("load", function () {
  // initialize all carousels
  $(".carousel").each(function () {
    const $carousel = $(this);

    $carousel.carousel();

    $carousel.on("slid.bs.carousel", function () {
      var idx = $carousel.find(".carousel-item.active").index(); // Get index of current active item within THIS carousel

      $carousel
        .find(".carousel-indicators li") // Select only indicators within THIS carousel
        .removeClass("active")
        .eq(idx)
        .addClass("active");
    });
  });
});

// Champion Skin Carousel
$(document).ready(function () {
  $("#championSkinsCarousel .carousel-item").first().addClass("active");
});

// Search Bar
$(function () {
  $("#search-input").autocomplete({
    source: function (request, response) {
      $.ajax({
        url: "/search",
        dataType: "json",
        data: {
          q: request.term,
        },
        success: function (data) {
          response(data);
        },
      });
    },
    minLength: 2,
    select: function (event, ui) {
      window.location.href = "/champion/" + ui.item.value;
    },
  });
});

// Favorite Toggling
$(document).on("click", "#favorite-btn", function () {
  const championId = $(this).data("champion-id");
  $.ajax({
    url: `/favorite/${championId}`,
    type: "POST",
    success: function (response) {
      if (response.is_authenticated === false) {
        alert("Please log in to favorite!");
      } else {
        let btn = $("#favorite-btn");
        if (response.is_favorited) {
          btn.text("Unfavorite");
          btn.removeClass("btn-primary").addClass("btn-warning");
        } else {
          btn.text("Favorite");
          btn.removeClass("btn-warning").addClass("btn-primary");
        }
      }
    },
    error: function (xhr, status, error) {
      if (xhr.status == 401) {
        alert("Please log in to favorite!");
      } else {
        // handle other errors
        console.error("An error occurred: ", error);
      }
    },
  });
});
