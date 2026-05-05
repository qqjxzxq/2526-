window.renderD3Network = function(combinedData) {
    // 1. 防御性检查
    if (typeof d3 === 'undefined' || typeof d3.contourDensity === 'undefined') {
        console.log("等待 D3 或插件加载...");
        setTimeout(() => window.renderD3Network(combinedData), 100);
        return;
    }

    const container = d3.select("#d3-viz-container");
    container.selectAll("*").remove();

    const fullWidth = container.node().clientWidth;
    const fullHeight = 900;
    const halfW = fullWidth / 2;
    const halfH = fullHeight / 2;

    const svg = container.append("svg")
        .attr("width", fullWidth)
        .attr("height", fullHeight)
        .style("background-color", "#FFFFFF");

    // 2. 样式配置 (复刻 Nature 风格)
    const viewConfigs = [
        { key: "left", xShift: 0, nodeColor: "#1A3678", edgeColor: "#4E5D8F" },
        { key: "right", xShift: halfW, nodeColor: "#2A8A96", edgeColor: "#66B191" }
    ];

    // 3. 统一比例尺 (固定 Domain 以实现跨年横向对比)
    const xScale = d3.scaleLinear().domain([-60, 60]).range([50, halfW - 50]);
    const yScale = d3.scaleLinear().domain([-60, 60]).range([50, halfH - 50]);

    viewConfigs.forEach(cfg => {
        const data = combinedData[cfg.key];
        const { nodes, links, year } = data;

        // --- 绘制上排：Temporal Structure (带 Hammer 边绑定模拟) ---
        const gNet = svg.append("g")
            .attr("transform", `translate(${cfg.xShift}, 0)`);

        gNet.append("text")
            .attr("x", halfW/2).attr("y", 40).attr("text-anchor", "middle")
            .style("font-family", "Arial, sans-serif").style("font-weight", "bold").style("font-size", "20px")
            .text(`Temporal Structure (${year})`);

        // Hammer 绑定模拟的核心：计算全局/局部重心
        const avgX = d3.mean(nodes, d => d.x);
        const avgY = d3.mean(nodes, d => d.y);

        const nodeMap = new Map(nodes.map(d => [d.id, d]));

        // 绘制连线
        gNet.append("g").selectAll("path")
            .data(links).enter().append("path")
            .attr("d", d => {
                const s = nodeMap.get(d.source), t = nodeMap.get(d.target);
                if(!s || !t) return null;

                const sx = xScale(s.x), sy = yScale(s.y);
                const tx = xScale(t.x), ty = yScale(t.y);

                // 计算直线中点
                const midX = (sx + tx) / 2;
                const midY = (sy + ty) / 2;

                /**
                 * Hammer 效果核心逻辑：
                 * 我们将每条边的贝塞尔控制点向点群的“重心”拉引。
                 * bundleStrength (0-1): 越大，边绑定越紧密。
                 */
                const bundleStrength = 0.5; 
                const cpX = midX + (xScale(avgX) - midX) * bundleStrength;
                const cpY = midY + (yScale(avgY) - midY) * bundleStrength;

                // 使用二次贝塞尔曲线：M 起点 Q 控制点 终点
                return `M${sx},${sy} Q${cpX},${cpY} ${tx},${ty}`;
            })
            .attr("fill", "none")
            .attr("stroke", cfg.edgeColor)
            .attr("stroke-width", 0.5) // 绑定后线可以稍微加粗一点点
            .attr("stroke-opacity", 0.15) // 低透明度是产生“束拢感”的关键
            .style("mix-blend-mode", "multiply"); // 增加线条重叠处的深浅变化

        // 绘制节点
        gNet.append("g").selectAll("circle")
            .data(nodes).enter().append("circle")
            .attr("r", 2.2).attr("cx", d => xScale(d.x)).attr("cy", d => yScale(d.y))
            .attr("fill", cfg.nodeColor).attr("opacity", 0.8);


        // --- 绘制下排：Knowledge Hotspots (保持不变) ---
        const gHot = svg.append("g")
            .attr("transform", `translate(${cfg.xShift}, ${halfH})`);

        gHot.append("text")
            .attr("x", halfW/2).attr("y", 30).attr("text-anchor", "middle")
            .style("font-family", "Arial, sans-serif").style("font-weight", "bold").style("font-size", "20px")
            .text(`Knowledge Hotspots (${year})`);

        const colorScale = d3.scaleLinear()
            .domain([0, 0.5, 1])
            .range(["#FFFFFF", cfg.edgeColor, cfg.nodeColor]);

        const contours = d3.contourDensity()
            .x(d => xScale(d.x)).y(d => yScale(d.y))
            .size([halfW, halfH]).bandwidth(25).thresholds(20)(nodes);

        const maxVal = d3.max(contours, d => d.value);

        gHot.append("g").selectAll("path")
            .data(contours).enter().append("path")
            .attr("d", d3.geoPath())
            .attr("fill", d => colorScale(d.value / maxVal))
            .attr("opacity", 0.85);
    });
};