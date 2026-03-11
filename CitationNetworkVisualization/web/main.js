// --- 1. 基础配置 ---
const chartDiv = document.getElementById("chart");
const rect = chartDiv.getBoundingClientRect();
const width = rect.width || window.innerWidth;
const height = window.innerHeight * 0.85;

let currentView = 'force'; 
let nodes = [], links = [];
let nodeSelection, linkSelection, simulation; 

const svg = d3.select("#chart").append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("width", "100%").attr("height", height)
  .style("background-color", "#1a1a1a");

const container = svg.append("g");
const zoom = d3.zoom().scaleExtent([0.01, 20]).on("zoom", (e) => container.attr("transform", e.transform));
svg.call(zoom);

// --- 2. 核心视图切换逻辑 ---
function switchView(viewType) {
    currentView = viewType;
    if (!nodeSelection) return;

    
    if (viewType === 'force') {
        simulation.alpha(1).restart();
        linkSelection.transition().duration(500).style("opacity", 0.3);
    } else {
        simulation.stop();
        const validNodes = nodes.filter(d => d[`x_${viewType}`] !== undefined);
        if (validNodes.length === 0) return;

        const padding = 80;
        const xScale = d3.scaleLinear()
            .domain(d3.extent(validNodes, d => d[`x_${viewType}`]))
            .range([padding, width - padding]);
        const yScale = d3.scaleLinear()
            .domain(d3.extent(validNodes, d => d[`y_${viewType}`]))
            .range([padding, height - padding]);

        nodeSelection.transition()
            .duration(1500)
            .ease(d3.easeExpOut)
            .style("opacity", d => d[`x_${viewType}`] !== undefined ? 1 : 0.05)
            .attr("cx", d => d[`x_${viewType}`] !== undefined ? xScale(d[`x_${viewType}`]) : width/2)
            .attr("cy", d => d[`y_${viewType}`] !== undefined ? yScale(d[`y_${viewType}`]) : height/2);

        linkSelection.transition()
            .duration(1500)
            .style("opacity", 0.05)
            .attr("x1", d => xScale(d.source[`x_${viewType}`] || 0))
            .attr("y1", d => yScale(d.source[`y_${viewType}`] || 0))
            .attr("x2", d => xScale(d.target[`x_${viewType}`] || 0))
            .attr("y2", d => yScale(d.target[`y_${viewType}`] || 0));
    }

    
    // 移除所有按钮的 active 类
    d3.selectAll(".btn-group button").classed("active", false);
    
    // 给当前点击的按钮添加 active 类
    // 注意：这里需要确保你的 HTML 按钮逻辑能传递按钮本身，或者通过 viewType 匹配
    if (viewType === 'force') d3.select("#btn-force").classed("active", true);
    if (viewType === 'topo') d3.select("#btn-topo").classed("active", true);
    if (viewType === 'hybrid') d3.select("#btn-hybrid").classed("active", true);
}

// --- 3. 数据加载逻辑 ---
function loadYear(year) {
  container.selectAll("*").remove();
  d3.json(`data/${year}.json`).then(data => {
    nodes = data.nodes;
    links = data.links;

    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(50))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2));

    linkSelection = container.append("g").selectAll("line")
      .data(links).join("line")
      .attr("stroke", "#666").attr("stroke-width", 1).attr("opacity", 0.3);

    nodeSelection = container.append("g").selectAll("circle")
      .data(nodes).join("circle")
      .attr("r", d => Math.max(3, Math.sqrt(d.citations || 1) * 2))
      .attr("fill", d => d3.interpolateViridis((d.year - 1986) / 40))
      .attr("stroke", "#fff").attr("stroke-width", 0.5)
      .call(d3.drag() // 直接把 drag 写在这里，防止报错
        .on("start", (e, d) => {
            if (!e.active && currentView === 'force') simulation.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
        })
        .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on("end", (e, d) => {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null; d.fy = null;
        })
      );

    simulation.on("tick", () => {
      if (currentView === 'force') {
        linkSelection.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                     .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        nodeSelection.attr("cx", d => d.x).attr("cy", d => d.y);
      }
    });

    // 关键：保持当前用户的视角
    switchView(currentView);

  });
}



// 初始化年份列表
const yearSelect = document.getElementById("yearSelect");
const startYear = 1986;
const endYear = 2025;

for (let y = startYear; y <= endYear; y++) {
  const opt = document.createElement("option");
  opt.value = y;
  opt.innerText = y + " 年";
  yearSelect.appendChild(opt);
}

// 绑定事件
yearSelect.onchange = () => loadYear(yearSelect.value);

// 默认加载
loadYear(1990);