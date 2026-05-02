window.renderD3Network = function(data) {
    const { nodes, links, year } = data;
    const container = d3.select("#d3-viz-container");
    container.selectAll("*").remove();

    const width = container.node().clientWidth / 2; // 分为左右两半
    const height = 800;

    // --- 颜色配置 (复现你的 Python 定义) ---
    const C_T1_NODE = "#1A3678";   
    const C_T1_EDGE = "#4E5D8F";   
    const C_T2_NODE = "#2A8A96";   // 如果是 2024 年可以用这个色系
    const C_T2_EDGE = "#66B191";   
    
    // 根据年份自动选择色系
    const isLateYear = year >= 2020;
    const nodeColor = isLateYear ? C_T2_NODE : C_T1_NODE;
    const edgeColor = isLateYear ? C_T2_EDGE : C_T1_EDGE;

    // 定义渐变色 (用于密度图)
    const colorScale = d3.scaleLinear()
        .domain([0, 0.5, 1])
        .range(["#FFFFFF", edgeColor, nodeColor]);

    // 创建主画布
    const mainSvg = container.append("svg")
        .attr("width", "100%")
        .attr("height", height)
        .style("background-color", "#FFFFFF");

    // 建立两个分组 G
    const gStructure = mainSvg.append("g").attr("transform", `translate(0,0)`);
    const gHotspots = mainSvg.append("g").attr("transform", `translate(${width},0)`);

    // 比例尺
    const xScale = d3.scaleLinear()
        .domain(d3.extent(nodes, d => d.x)).range([50, width - 50]);
    const yScale = d3.scaleLinear()
        .domain(d3.extent(nodes, d => d.y)).range([50, height - 50]);

    // 映射表
    const nodeMap = new Map(nodes.map(d => [d.id, d]));

    // --- A. 复现 Temporal Structure (左侧) ---
    // 模拟 Hammer Bundle 的边路径
    const lineGen = d3.line()
        .x(d => xScale(d.x))
        .y(d => yScale(d.y))
        .curve(d3.curveBundle.beta(0.85));

    gStructure.append("g")
        .selectAll("path")
        .data(links)
        .enter().append("path")
        .attr("d", d => {
            const s = nodeMap.get(d.source), t = nodeMap.get(d.target);
            if(!s || !t) return null;
            // 插入中点控制位移，模拟捆绑感
            const mid = { x: (s.x + t.x) / 2 * 0.9, y: (s.y + t.y) / 2 * 0.9 };
            return lineGen([s, mid, t]);
        })
        .attr("fill", "none")
        .attr("stroke", edgeColor)
        .attr("stroke-width", 0.6)
        .attr("stroke-opacity", 0.25);

    gStructure.append("g")
        .selectAll("circle")
        .data(nodes)
        .enter().append("circle")
        .attr("r", 2.5)
        .attr("cx", d => xScale(d.x))
        .attr("cy", d => yScale(d.y))
        .attr("fill", nodeColor)
        .attr("fill-opacity", 0.8);

    gStructure.append("text")
        .attr("x", width/2).attr("y", 30).attr("text-anchor", "middle")
        .style("font-weight", "bold").style("font-size", "20px")
        .text(`Temporal Structure (${year})`);

    // --- B. 复现 Knowledge Hotspots (右侧密度图) ---
    // 1. 生成密度数据 (类似 Seaborn KDE)
    const contourData = d3.contourDensity()
        .x(d => xScale(d.x))
        .y(d => yScale(d.y))
        .size([width, height])
        .bandwidth(15) // 控制平滑度
        .thresholds(20) // 控制等高线层数
        (nodes);

    const maxVal = d3.max(contourData, d => d.value);

    gHotspots.append("g")
        .selectAll("path")
        .data(contourData)
        .enter().append("path")
        .attr("d", d3.geoPath())
        .attr("fill", d => colorScale(d.value / maxVal))
        .attr("stroke", "none")
        .attr("opacity", 0.9);

    gHotspots.append("text")
        .attr("x", width/2).attr("y", 30).attr("text-anchor", "middle")
        .style("font-weight", "bold").style("font-size", "20px")
        .text(`Knowledge Hotspots (${year})`);
};