import React from "react";
import ApexCharts from "react-apexcharts";

const ProductDetailsPage = ({ product }) => {
  const {
    name,
    url: productUrl,
    img,
    source,
    created_at: createdAt,
    priceHistory,
  } = product;

  function formatDate(date) {
    const options = {
      timeZone: "Asia/Bangkok", // GMT+7 timezone
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false, // Use 24-hour format
    };
  
    const formattedDate = new Intl.DateTimeFormat("en-US", options).format(date);
  
    // Convert formattedDate to "yyyy-MM-dd HH:mm:ss" format
    const [datePart, timePart] = formattedDate.split(", ");
    const [month, day, year] = datePart.split("/");
    return `${year}-${month}-${day} ${timePart}`;
  }

  const dates = priceHistory
    .map((history) => formatDate(new Date(history.date)))
    .reverse();
  const prices = priceHistory.map((history) => history.price).reverse();

  const chartData = {
    options: {
      chart: {
        id: "price-chart",
      },
      xaxis: {
        categories: dates, // Example categories (dates)
      },
    },
    series: [
      {
        name: "Price",
        data: prices, // Example data
      },
    ],
  };

  return (
    <div>
      <h2>{name}</h2>
      <img src={img} alt="Product" />
      <p>
        URL:{" "}
        <a href={`${source}${productUrl}`} target="_blank">
          View product.
        </a>
      </p>
      <p>
        Source:{" "}
        <a target="_blank" href={source}>
          {source}
        </a>
      </p>
      <p>Newest Price At: {createdAt}</p>
      <h2>Price History</h2>
      <h3>
        Current Price: ${prices.length > 0 ? prices[prices.length - 1] : "N/A"}
      </h3>
      <ApexCharts
        options={chartData.options}
        series={chartData.series}
        type="line"
        height={300}
      />
    </div>
  );
};

export default ProductDetailsPage;
