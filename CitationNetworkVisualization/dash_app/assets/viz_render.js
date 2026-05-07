window.renderD3Network = function(combinedData) {
    if (typeof d3 === 'undefined' || typeof d3.contourDensity === 'undefined') {
        setTimeout(() => window.renderD3Network(combinedData), 100);
        return;
    }

    const container = d3.select("#d3-viz-container");
    container.selectAll("*").remove();

    // 计算布局：左侧 80% 绘图，右侧 20% 信息
    const totalWidth = container.node().clientWidth;
    const vizWidth = totalWidth * 0.78;
    const infoWidth = totalWidth * 0.2;
    const fullHeight = 900;
    const halfW = vizWidth / 2;
    const halfH = fullHeight / 2;

    // 创建主容器
    const mainWrapper = container.append("div")
        .style("display", "flex")
        .style("flex-direction", "row");

    // 左侧：SVG 绘图区
    const svg = mainWrapper.append("svg")
        .attr("width", vizWidth)
        .attr("height", fullHeight)
        .style("background-color", "#FFFFFF")
        .style("border-right", "1px solid #eee");

    // 右侧：信息卡面板 (View 5)
    const infoPanel = mainWrapper.append("div")
        .attr("id", "detail-spec-panel")
        .style("width", `${infoWidth}px`)
        .style("padding", "20px")
        .style("background", "#f9f9f9")
        .style("overflow-y", "auto")
        .html(`
            <h3 style="border-bottom:2px solid #333; padding-bottom:10px;">论文详情</h3>
            <div id="info-content" style="color:#666; line-height:1.6;">
                <p>请悬停在节点上查看数据...</p>
            </div>
        `);

    // 比例尺
    const xScale = d3.scaleLinear().domain([-60, 60]).range([50, halfW - 50]);
    const yScale = d3.scaleLinear().domain([-60, 60]).range([50, halfH - 50]);

    const lineGenerator = d3.line().curve(d3.curveBasis)
        .x(d => xScale(d[0])).y(d => yScale(d[1]));

    // 协同缩放组
    const zoomGroupLeft = svg.append("g");
    const zoomGroupRight = svg.append("g").attr("transform", `translate(${halfW}, 0)`);

    const zoom = d3.zoom().on("zoom", (e) => {
        d3.select("#content-left").attr("transform", e.transform);
        d3.select("#content-right").attr("transform", e.transform);
    });
    svg.call(zoom);

    const viewConfigs = [
        { key: "left", container: zoomGroupLeft, xShift: 0, nodeColor: "#1A3678", edgeColor: "#4E5D8F" },
        { key: "right", container: zoomGroupRight, xShift: halfW, nodeColor: "#2A8A96", edgeColor: "#66B191" }
    ];

    viewConfigs.forEach(cfg => {
        const data = combinedData[cfg.key];
        const { nodes, links, year } = data;

        // 绘制上排网络
        cfg.container.append("text")
            .attr("x", halfW/2).attr("y", 30).attr("text-anchor", "middle")
            .style("font-weight", "bold").text(`Network Structure (${year})`);

        const content = cfg.container.append("g").attr("id", `content-${cfg.key}`);

        // 1. 建立节点查找表 (优化查询效率)
        const nodeMap = new Map(nodes.map(d => [String(d.id), d]));

        // 2. 绘制连线
        content.append("g")
            .selectAll("path")
            .data(links)
            .enter()
            .append("path")
            .attr("d", d => {
                // 根据 ID 获取起点和终点节点
                const s = nodeMap.get(String(d.source));
                const t = nodeMap.get(String(d.target));
                
                if (!s || !t) return null;

                // 将原始坐标转换为像素坐标
                const sx = xScale(s.x), sy = yScale(s.y);
                const tx = xScale(t.x), ty = yScale(t.y);

                // --- 模拟 Hammer Bundle 效果的核心逻辑 ---
                // 计算直线中点
                const midX = (sx + tx) / 2;
                const midY = (sy + ty) / 2;

                // 计算点群的重心 (用于引力拉引)
                const avgX = xScale(d3.mean(nodes, n => n.x));
                const avgY = yScale(d3.mean(nodes, n => n.y));

                // bundleStrength 控制弯曲程度 (0: 直线, 1: 全部拉到重心)
                const bundleStrength = 0.6; 
                const cpX = midX + (avgX - midX) * bundleStrength;
                const cpY = midY + (avgY - midY) * bundleStrength;

                // 返回二次贝塞尔曲线路径：M起点 Q控制点 终点
                return `M${sx},${sy} Q${cpX},${cpY} ${tx},${ty}`;
            })
            .attr("fill", "none")
            .attr("stroke", cfg.edgeColor)
            .attr("stroke-width", 0.7) // 稍微加粗一点
            .attr("stroke-opacity", 0.15)
            .style("mix-blend-mode", "multiply")
            .style("pointer-events", "none");

        // 节点
        content.append("g").selectAll("circle").data(nodes).enter().append("circle")
            .attr("r", 2.5).attr("cx", d => xScale(d.x)).attr("cy", d => yScale(d.y))
            .attr("fill", cfg.nodeColor).attr("opacity", 0.8)
            .on("mouseover", function(e, d) {
                d3.select(this).attr("r", 6).attr("fill", "#FF5722");
                
                // 更新右侧信息卡 (联动核心)
                d3.select("#info-content").html(`
                    <div style="margin-bottom:15px;">
                        <b style="color:#333;">ID:</b><br/>${d.id}
                    </div>
                    <div style="margin-bottom:15px;">
                        <b style="color:#333;">年份:</b><br/>${d.year}
                    </div>
                    <div style="margin-bottom:15px;">
                        <b style="color:#333;">坐标:</b><br/>X: ${d.x.toFixed(2)}<br/>Y: ${d.y.toFixed(2)}
                    </div>
                    <p style="font-size:0.9em; color:#888;">提示：该坐标反映了论文在学术空间中的语义位置。</p>
                `);
            })
            .on("mouseout", function() {
                d3.select(this).attr("r", 2.5).attr("fill", cfg.nodeColor);
            });

        // 绘制下排密度 (View 3 & 4)
        const gHot = svg.append("g").attr("transform", `translate(${cfg.xShift}, ${halfH})`);
        gHot.append("text").attr("x", halfW/2).attr("y", 25).attr("text-anchor", "middle")
            .style("font-weight", "bold").text(`Hotspots (${year})`);

        const contours = d3.contourDensity()
            .x(d => xScale(d.x)).y(d => yScale(d.y))
            .size([halfW, halfH]).bandwidth(25).thresholds(20)(nodes);

        const maxVal = d3.max(contours, d => d.value);
        const colorScale = d3.scaleLinear().domain([0, 1]).range(["#FFFFFF", cfg.nodeColor]);

        gHot.append("g").selectAll("path").data(contours).enter().append("path")
            .attr("d", d3.geoPath())
            .attr("fill", d => colorScale(d.value / maxVal)).attr("opacity", 0.7);
    });
};