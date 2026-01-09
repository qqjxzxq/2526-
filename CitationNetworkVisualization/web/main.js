const width = window.innerWidth;
const height = window.innerHeight * 0.9;

const svg = d3.select("#chart")
  .append("svg")
  .attr("width", width)
  .attr("height", height);

// 创建容器用于缩放和平移
const container = svg.append("g");

// 添加缩放行为
const zoom = d3.zoom()
  .scaleExtent([0.1, 4])  // 缩放范围：0.1倍到4倍
  .on("zoom", (event) => {
    container.attr("transform", event.transform);
  });

svg.call(zoom);

const yearSelect = document.getElementById("yearSelect");

async function loadYearList() {
  const res = await fetch("data/");
}

function loadYear(year) {
  // 只清除容器内容，保留缩放状态
  container.selectAll("*").remove();

  d3.json(`data/${year}.json`).then(data => {

    const nodes = data.nodes;
    const links = data.links;

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-120))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // 将链接和节点都添加到容器中
    const link = container.append("g")
      .attr("stroke", "#333333")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 1)
      .attr("opacity", 0.4);

    const node = container.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", d => Math.max(3, Math.sqrt(d.citations)))
      .attr("fill", d => d3.interpolateViridis(d.citations / 60))
      .call(drag(simulation));

    node.append("title")
      .text(d => `ID: ${d.id}\nCitations: ${d.citations}`);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
    });
  });
}

function drag(simulation) {
  return d3.drag()
    .on("start", event => {
      // 阻止缩放行为，只允许拖拽节点
      if (event.sourceEvent) {
        event.sourceEvent.stopPropagation();
      }
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    })
    .on("drag", event => {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    })
    .on("end", event => {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    });
}

// init years
const years = Array.from({length: 2025-1986+1}, (_,i)=>1986+i);
years.forEach(y=>{
  const opt=document.createElement("option");
  opt.value=y; opt.innerText=y;
  yearSelect.appendChild(opt);
});

yearSelect.onchange = () => loadYear(yearSelect.value);
loadYear(1990);
