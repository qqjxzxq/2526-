window.renderD3Network = function(combinedData) {
    if (typeof d3 === 'undefined' || typeof d3.contourDensity === 'undefined') {
        setTimeout(() => window.renderD3Network(combinedData), 100);
        return;
    }

    const container = d3.select("#d3-viz-container");
    container.selectAll("*").remove();

    // 辅助函数：统一 ID 格式化，确保匹配准确
    const cleanIdFunc = (id) => String(id).replace("https://openalex.org/", "").replace(/[^a-zA-Z0-9]/g, '');

    // --- 1. 预处理：从右侧年份提取所有引用的 ID 集合 ---
    const citedSet = new Set();
    const citedCountMap = new Map();
    if (combinedData.right && combinedData.right.nodes) {
        combinedData.right.nodes.forEach(node => {
            if (node.ref_list && Array.isArray(node.ref_list)) {
                node.ref_list.forEach(refId => {
                    const cid = cleanIdFunc(refId);

                    citedSet.add(cid);

                    citedCountMap.set(
                        cid,
                        (citedCountMap.get(cid) || 0) + 1
                    );
                });
            }
        });
    }

    console.log("========== DEBUG ==========");

    console.log(
        "citedSet sample:",
        [...citedSet].slice(0, 10)
    );

    console.log(
        "left node sample:",
        combinedData.left.nodes
            .slice(0, 10)
            .map(d => cleanIdFunc(d.id))
    );

    // --- 2. 布局初始化 ---
    const totalWidth = container.node().clientWidth;
    const vizWidth = totalWidth * 0.78;
    const infoWidth = totalWidth * 0.22;
    const fullHeight = 900;
    const halfW = vizWidth / 2;
    const halfH = fullHeight / 2;

    // ===== 知识演化说明 =====
    container.append("div")
        .style("padding", "10px 18px")
        .style("background", "#fff5fa")
        .style("border-left", "5px solid #E91E63")
        .style("margin", "10px 20px")
        .style("border-radius", "8px")
        .style("font-size", "13px")
        .style("color", "#444")
        .html(`
            <b style="color:#E91E63;">粉色节点</b>
            表示：
            左侧年份中被右侧年份论文引用的研究工作，
            体现了知识在时间中的延续与传播。
        `);

    const mainWrapper = container.append("div")
        .style("display", "flex")
        .style("width", "100%")
        .style("height", `${fullHeight}px`);

    const svg = mainWrapper.append("svg")
        .attr("width", vizWidth)
        .attr("height", fullHeight)
        .style("background-color", "#FFFFFF")
        .style("border-right", "1px solid #eee");
    
        // ===== Legend =====
    const legend = svg.append("g")
        .attr("transform", "translate(20,20)");

    // 普通节点
    legend.append("circle")
        .attr("r", 5)
        .attr("cx", 0)
        .attr("cy", 0)
        .attr("fill", "#1A3678");

    legend.append("text")
        .attr("x", 12)
        .attr("y", 4)
        .style("font-size", "12px")
        .text("普通论文");

    // 被未来引用
    legend.append("circle")
        .attr("r", 5)
        .attr("cx", 0)
        .attr("cy", 22)
        .attr("fill", "#E91E63");

    legend.append("text")
        .attr("x", 12)
        .attr("y", 26)
        .style("font-size", "12px")
        .text("被未来研究引用");

    // 当前 hover
    legend.append("circle")
        .attr("r", 5)
        .attr("cx", 0)
        .attr("cy", 44)
        .attr("fill", "#FF5722");

    legend.append("text")
        .attr("x", 12)
        .attr("y", 48)
        .style("font-size", "12px")
        .text("当前选中节点");

    const infoPanel = mainWrapper.append("div")
        .attr("id", "detail-panel")
        .style("width", `${infoWidth}px`)
        .style("padding", "25px")
        .style("background", "#fcfcfc")
        .style("overflow-y", "auto")
        .html(`
            <h3 style="border-bottom:2px solid #1A3678; padding-bottom:10px; color:#1A3678; margin-top:0;">论文详情</h3>
            <div id="info-content"><p style="color:#999; margin-top:20px;">鼠标悬停在节点上查看详情。</p></div>
        `);

    const updateInfoContent = (d) => {
        const authorList = d.authorNamesDeduped ? d.authorNamesDeduped.replace(/;/g, ", ") : "Unknown Authors";
        const futureInfluence =
            citedCountMap.get(cleanIdFunc(d.id)) || 0;
        d3.select("#info-content").html(`
            <div style="
                margin-bottom: 15px;
                padding: 10px;
                background: #fff5fa;
                border-left: 4px solid #E91E63;
                border-radius: 6px;
            ">
                <b style="color:#E91E63;">
                    Future Influence:
                </b>

                <div style="margin-top:5px; font-size:0.85em;">
                    被未来年份论文引用
                    <b>${futureInfluence}</b>
                    次
                </div>
            </div>
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
                <div style="font-size: 0.85em; color: #666; line-height: 1.5; text-align: justify; max-height: 300px; overflow-y: auto;">
                    ${d.abstract || 'No abstract available.'}
                </div>
            </div>
            <div style="border-top: 1px dotted #ccc; padding-top: 10px; font-size: 0.75em; color: #999;">
                <b>Citations:</b> ${d.oa_cited_by_count || 0} | <b>ID:</b> ${d.id}
            </div>
        `);
    };

    const xScale = d3.scaleLinear().domain([-60, 60]).range([50, halfW - 50]);
    const yScale = d3.scaleLinear().domain([-60, 60]).range([50, halfH - 50]);

    const lineFunc = (s, t, nodes) => {
        const sx = xScale(s.x), sy = yScale(s.y), tx = xScale(t.x), ty = yScale(t.y);
        const midX = (sx + tx) / 2, midY = (sy + ty) / 2;
        const avgX = xScale(d3.mean(nodes, n => n.x)), avgY = yScale(d3.mean(nodes, n => n.y));
        const cpX = midX + (avgX - midX) * 0.6, cpY = midY + (avgY - midY) * 0.6;
        return `M${sx},${sy} Q${cpX},${cpY} ${tx},${ty}`;
    };

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
            .style("font-weight", "bold").text(`Year: ${year}`);

        const content = cfg.group.append("g").attr("id", `content-${cfg.idSuffix}`);

        content.append("g").selectAll("path").data(links).enter().append("path")
            .attr("d", d => {
                const s = nodeMap.get(String(d.source)), t = nodeMap.get(String(d.target));
                return (s && t) ? lineFunc(s, t, nodes) : null;
            })
            .attr("fill", "none").attr("stroke", cfg.color).attr("stroke-opacity", 0.12);

        content.append("g").selectAll("circle").data(nodes).enter().append("circle")
            .attr("class", d => {
                const cleanId = cleanIdFunc(d.id);
                return `node-dot dot-${cfg.idSuffix} id-${cleanId}`;
            })
            .attr("r", 2.8).attr("cx", d => xScale(d.x)).attr("cy", d => yScale(d.y))
            .attr("fill", d => {
                // 直接渲染高亮逻辑：如果是左图且在引用集合中，设为洋红色
                const cid = cleanIdFunc(d.id);
                if (cfg.idSuffix === "L" && citedSet.has(cid)) return "#E91E63";
                return cfg.color;
            })
            .attr("opacity", 0.8)
            .style("cursor", "pointer")
            .on("mouseover", function(e, d) {
                // 1. 本点高亮（橙色描边）
                d3.select(this).attr("r", 8).attr("fill", "#FF5722").attr("stroke", "#000").attr("stroke-width", 2);
                
                // 2. 更新面板
                updateInfoContent(d);

                // 3. 引用溯源交互（右图触发时）
                if (cfg.idSuffix === "R" && d.ref_list) {
                    d3.selectAll(".dot-L").attr("opacity", 0.15); // 背景淡化
                    d.ref_list.forEach(refId => {
                        const targetId = cleanIdFunc(refId);
                        d3.selectAll(`.dot-L.id-${targetId}`)
                            .attr("r", 6).attr("fill", "#E91E63").attr("opacity", 1)
                            .attr("stroke", "#000").attr("stroke-width", 1.5);
                    });
                }
            })
            .on("mouseout", function(e, d) {
                const cid = cleanIdFunc(d.id);
                const isOriginallyCited = (cfg.idSuffix === "L" && citedSet.has(cid));
                
                // 恢复本点状态
                d3.select(this)
                    .attr("r", 2.8)
                    .attr("fill", isOriginallyCited ? "#E91E63" : cfg.color)
                    .attr("stroke", "none");

                // 如果是右图移出，恢复左图所有点
                if (cfg.idSuffix === "R") {
                    d3.selectAll(".dot-L")
                        .attr("r", 2.8)
                        .attr("opacity", 0.8)
                        .attr("stroke", "none")
                        .attr("fill", function() {
                            // 检查该点原本是否在 citedSet 中
                            const cls = d3.select(this).attr("class");
                            const match = cls.match(/id-([a-zA-Z0-9]+)/);
                            const thisId = match ? match[1] : null;
                            return (thisId && citedSet.has(thisId)) ? "#E91E63" : "#1A3678";
                        });
                }
            });

        // 密度图保持不变
        const gHot = svg.append("g").attr("transform", `translate(${cfg.xShift}, ${halfH})`);
        const contours = d3.contourDensity().x(d => xScale(d.x)).y(d => yScale(d.y)).size([halfW, halfH]).bandwidth(25).thresholds(20)(nodes);
        const colorScale = d3.scaleLinear().domain([0, d3.max(contours, d => d.value)]).range(["#FFFFFF", cfg.color]);
        gHot.append("g").selectAll("path").data(contours).enter().append("path").attr("d", d3.geoPath()).attr("fill", d => colorScale(d.value)).attr("opacity", 0.7);
    });
};