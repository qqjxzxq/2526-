window.renderD3Network = function(combinedData) {
    if (typeof d3 === 'undefined' || typeof d3.contourDensity === 'undefined') {
        setTimeout(() => window.renderD3Network(combinedData), 100);
        return;
    }

    const container = d3.select("#d3-viz-container");
    container.selectAll("*").remove();

    // --- 1. 布局初始化：左侧绘图，右侧信息栏 ---
    const totalWidth = container.node().clientWidth;
    const vizWidth = totalWidth * 0.78; // 绘图区占 78%
    const infoWidth = totalWidth * 0.22; // 信息栏占 22%
    const fullHeight = 900;
    const halfW = vizWidth / 2;
    const halfH = fullHeight / 2;

    const mainWrapper = container.append("div")
        .style("display", "flex")
        .style("flex-direction", "row")
        .style("width", "100%")
        .style("height", `${fullHeight}px`);

    // 左侧：SVG 画布
    const svg = mainWrapper.append("svg")
        .attr("width", vizWidth)
        .attr("height", fullHeight)
        .style("background-color", "#FFFFFF")
        .style("border-right", "1px solid #eee");

    // 右侧：常驻信息面板
    const infoPanel = mainWrapper.append("div")
        .attr("id", "detail-panel")
        .style("width", `${infoWidth}px`)
        .style("height", `${fullHeight}px`)
        .style("padding", "25px")
        .style("background", "#fcfcfc")
        .style("overflow-y", "auto")
        .style("box-sizing", "border-box")
        .html(`
            <h3 style="border-bottom:2px solid #1A3678; padding-bottom:10px; color:#1A3678; margin-top:0;">论文详情</h3>
            <div id="info-content">
                <p style="color:#999; margin-top:20px;">鼠标悬停在节点上，查看论文的完整元数据（标题、作者、摘要）。</p>
            </div>
        `);

    // --- 2. 比例尺与配置 ---
    const xScale = d3.scaleLinear().domain([-60, 60]).range([50, halfW - 50]);
    const yScale = d3.scaleLinear().domain([-60, 60]).range([50, halfH - 50]);

    // 定义二次贝塞尔曲线生成器 (用于手动模拟边绑定)
    const lineFunc = (s, t, nodes) => {
        const sx = xScale(s.x), sy = yScale(s.y);
        const tx = xScale(t.x), ty = yScale(t.y);
        const midX = (sx + tx) / 2, midY = (sy + ty) / 2;
        const avgX = xScale(d3.mean(nodes, n => n.x));
        const avgY = yScale(d3.mean(nodes, n => n.y));
        const bundleStrength = 0.6;
        const cpX = midX + (avgX - midX) * bundleStrength;
        const cpY = midY + (avgY - midY) * bundleStrength;
        return `M${sx},${sy} Q${cpX},${cpY} ${tx},${ty}`;
    };

    // 协同缩放组
    const gLeft = svg.append("g");
    const gRight = svg.append("g").attr("transform", `translate(${halfW}, 0)`);

    const zoom = d3.zoom().on("zoom", (e) => {
        d3.select("#content-L").attr("transform", e.transform);
        d3.select("#content-R").attr("transform", e.transform);
    });
    svg.call(zoom);

    const configs = [
        { key: "left", group: gLeft, xShift: 0, color: "#1A3678", idSuffix: "L" },
        { key: "right", group: gRight, xShift: halfW, color: "#2A8A96", idSuffix: "R" }
    ];

    configs.forEach(cfg => {
        const data = combinedData[cfg.key];
        const { nodes, links, year } = data;
        const nodeMap = new Map(nodes.map(d => [String(d.id), d]));

        cfg.group.append("text")
            .attr("x", halfW / 2).attr("y", 30).attr("text-anchor", "middle")
            .style("font-weight", "bold").style("font-size", "16px").text(`Year: ${year}`);

        const content = cfg.group.append("g").attr("id", `content-${cfg.idSuffix}`);

        // 绘制连线
        content.append("g").selectAll("path").data(links).enter().append("path")
            .attr("d", d => {
                const s = nodeMap.get(String(d.source)), t = nodeMap.get(String(d.target));
                return (s && t) ? lineFunc(s, t, nodes) : null;
            })
            .attr("fill", "none").attr("stroke", cfg.color).attr("stroke-opacity", 0.12);

        // 绘制节点
        content.append("g").selectAll("circle").data(nodes).enter().append("circle")
            .attr("r", 2.8).attr("cx", d => xScale(d.x)).attr("cy", d => yScale(d.y))
            .attr("fill", cfg.color).attr("opacity", 0.8)
            .style("cursor", "pointer")
            .on("mouseover", function(e, d) {
                // 1. 视觉反馈
                d3.select(this).attr("r", 7).attr("fill", "#FF5722");

                // 2. 更新侧边信息面板 (核心更新点)
                const authorList = d.authorNamesDeduped ? d.authorNamesDeduped.replace(/;/g, ", ") : "Unknown Authors";
                
                d3.select("#info-content").html(`
                    <div style="margin-bottom: 20px;">
                        <h4 style="color: #1A3678; margin: 0 0 8px 0; line-height: 1.3;">${d.title || 'No Title'}</h4>
                        <div style="font-size: 0.8em; color: #888;">
                            <span style="background:#eee; padding:2px 5px; border-radius:3px; margin-right:5px;">${d.conference || 'VIS'}</span>
                            <span>${d.year}</span>
                        </div>
                    </div>

                    <div style="margin-bottom: 15px;">
                        <b style="font-size: 0.9em; display:block; margin-bottom:4px;">Authors:</b>
                        <div style="font-size: 0.85em; color: #444;">${authorList}</div>
                    </div>

                    <div style="margin-bottom: 15px;">
                        <b style="font-size: 0.9em; display:block; margin-bottom:4px;">Abstract:</b>
                        <div style="font-size: 0.85em; color: #666; line-height: 1.5; text-align: justify; max-height: 400px; overflow-y: auto; padding-right: 5px;">
                            ${d.abstract || 'No abstract available.'}
                        </div>
                    </div>

                    <div style="border-top: 1px dotted #ccc; padding-top: 10px; font-size: 0.75em; color: #999;">
                        <b>Citations:</b> ${d.oa_cited_by_count || 0}<br/>
                        <b>ID:</b> ${d.id}<br/>
                        <b>Position:</b> X:${d.x.toFixed(2)}, Y:${d.y.toFixed(2)}
                    </div>
                `);
            })
            .on("mouseout", function() {
                d3.select(this).attr("r", 2.8).attr("fill", cfg.color);
            });

        // 绘制下排密度图
        const gHot = svg.append("g").attr("transform", `translate(${cfg.xShift}, ${halfH})`);
        const contours = d3.contourDensity()
            .x(d => xScale(d.x)).y(d => yScale(d.y))
            .size([halfW, halfH]).bandwidth(25).thresholds(20)(nodes);
        
        const colorScale = d3.scaleLinear().domain([0, d3.max(contours, d => d.value)]).range(["#FFFFFF", cfg.color]);

        gHot.append("g").selectAll("path").data(contours).enter().append("path")
            .attr("d", d3.geoPath()).attr("fill", d => colorScale(d.value)).attr("opacity", 0.7);
    });
};