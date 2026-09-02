import { LOC as e, fmtDur as t, fmtSize as n } from "/js/core.js";
import { emptyStateHtml as r, noteHtml as i } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var a, o, s, c, l, u, d, f, p, m, h, g, _, v, y = {}, b = [], x = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, S = Array.isArray;
function C(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function w(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function T(e, t, n) {
	var r, i, o, s = {};
	for (o in t) o == "key" ? r = t[o] : o == "ref" ? i = t[o] : s[o] = t[o];
	if (arguments.length > 2 && (s.children = arguments.length > 3 ? a.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (o in e.defaultProps) s[o] === void 0 && (s[o] = e.defaultProps[o]);
	return E(e, s, r, i, null);
}
function E(e, t, n, r, i) {
	var a = {
		type: e,
		props: t,
		key: n,
		ref: r,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: i ?? ++s,
		__i: -1,
		__u: 0
	};
	return i == null && o.vnode != null && o.vnode(a), a;
}
function D(e) {
	return e.children;
}
function O(e, t) {
	this.props = e, this.context = t;
}
function k(e, t) {
	if (t == null) return e.__ ? k(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? k(e) : null;
}
function A(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = C({}, t);
		a.__v = t.__v + 1, o.vnode && o.vnode(a), V(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? k(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, U(r, a, i), t.__e = t.__ = null, a.__e != n && j(a);
	}
}
function j(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), j(e);
}
function M(e) {
	(!e.__d && (e.__d = !0) && c.push(e) && !N.__r++ || l != o.debounceRendering) && ((l = o.debounceRendering) || u)(N);
}
function N() {
	try {
		for (var e, t = 1; c.length;) c.length > t && c.sort(d), e = c.shift(), t = c.length, A(e);
	} finally {
		c.length = N.__r = 0;
	}
}
function P(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || b, v = t.length;
	for (c = F(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || y, p.__i = d, g = V(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && K(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = I(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function F(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = E(null, o, null, null, null) : S(o) ? o = e.__k[a] = E(D, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = E(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = L(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = k(s)), q(s, s));
	return r;
}
function I(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = I(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = k(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function L(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function R(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || x.test(t) ? n : n + "px";
}
function z(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || R(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || R(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(h, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[m] = r[m] : (n[m] = g, e.addEventListener(t, a ? v : _, a)) : e.removeEventListener(t, a ? v : _, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function B(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[p] == null) t[p] = g++;
			else if (t[p] < n[m]) return;
			return n(o.event ? o.event(t) : t);
		}
	};
}
function V(e, t, n, r, i, a, s, c, l, u) {
	var d, f, p, m, h, g, _, v, y, x, T, E, A, j, M, N, F = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (l = !!(32 & n.__u), a = [c = t.__e = n.__e]), (d = o.__b) && d(t);
	n: if (typeof F == "function") {
		f = s.length;
		try {
			if (y = t.props, x = F.prototype && F.prototype.render, T = (d = F.contextType) && r[d.__c], E = d ? T ? T.props.value : d.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (x ? t.__c = p = new F(y, E) : (t.__c = p = new O(y, E), p.constructor = F, p.render = J), T && T.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), x && p.__s == null && (p.__s = p.state), x && F.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = C({}, p.__s)), C(p.__s, F.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) x && F.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), x && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (x && F.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, E), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, E)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), b.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && s.push(p), c = k(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, E), x && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = E, p.props = y, p.__P = e, p.__e = !1, A = o.__r, j = 0, x) p.state = p.__s, p.__d = !1, A && A(t), d = p.render(p.props, p.state, p.context), b.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, A && A(t), d = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++j < 25);
			p.state = p.__s, p.getChildContext != null && (r = C(C({}, r), p.getChildContext())), x && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), M = d != null && d.type === D && d.key == null ? W(d.props.children) : d, c = P(e, S(M) ? M : [M], t, n, r, i, a, s, c, l, u), p.base = t.__e, t.__u &= -161, p.__h.length && s.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (s.length = f, t.__v = null, l || a != null) {
				if (e.then) {
					for (t.__u |= l ? 160 : 128; c && c.nodeType == 8 && c.nextSibling;) c = c.nextSibling;
					a != null && (a[a.indexOf(c)] = null), t.__e = c;
				} else if (a != null) for (N = a.length; N--;) w(a[N]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || H(t), o.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : c = t.__e = G(n.__e, t, n, r, i, a, s, l, u);
	return (d = o.diffed) && d(t), 128 & t.__u ? void 0 : c;
}
function H(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(H));
}
function U(e, t, n) {
	for (var r = 0; r < n.length; r++) K(n[r], n[++r], n[++r]);
	o.__c && o.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			o.__e(e, t.__v);
		}
	});
}
function W(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : S(e) ? e.map(W) : e.constructor === void 0 ? C({}, e) : null;
}
function G(e, t, n, r, i, s, c, l, u) {
	var d, f, p, m, h, g, _, v = n.props || y, b = t.props, x = t.type;
	if (x == "svg" ? i = "http://www.w3.org/2000/svg" : x == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", s != null) {
		for (d = 0; d < s.length; d++) if ((h = s[d]) && "setAttribute" in h == !!x && (x ? h.localName == x : h.nodeType == 3)) {
			e = h, s[d] = null;
			break;
		}
	}
	if (e == null) {
		if (x == null) return document.createTextNode(b);
		e = document.createElementNS(i, x, b.is && b), l &&= (o.__m && o.__m(t, s), !1), s = null;
	}
	if (x == null) v === b || l && e.data == b || (e.data = b);
	else {
		if (s = x == "textarea" && b.defaultValue != null ? null : s && a.call(e.childNodes), !l && s != null) for (v = {}, d = 0; d < e.attributes.length; d++) v[(h = e.attributes[d]).name] = h.value;
		for (d in v) h = v[d], d == "dangerouslySetInnerHTML" ? p = h : d == "children" || d in b || d == "value" && "defaultValue" in b || d == "checked" && "defaultChecked" in b || z(e, d, null, h, i);
		for (d in b) h = b[d], d == "children" ? m = h : d == "dangerouslySetInnerHTML" ? f = h : d == "value" ? g = h : d == "checked" ? _ = h : l && typeof h != "function" || v[d] === h || z(e, d, h, v[d], i);
		if (f) l || p && (f.__html == p.__html || f.__html == e.innerHTML) || (e.innerHTML = f.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), P(t.type == "template" ? e.content : e, S(m) ? m : [m], t, n, r, x == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, s, c, s ? s[0] : n.__k && k(n, 0), l, u), s != null) for (d = s.length; d--;) w(s[d]);
		l && x != "textarea" || (d = "value", x == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[d] || x == "progress" && !g || x == "option" && g != v[d]) && z(e, d, g, v[d], i), d = "checked", _ != null && _ != e[d] && z(e, d, _, v[d], i));
	}
	return e;
}
function K(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		o.__e(e, n);
	}
}
function q(e, t, n) {
	var r, i;
	if (o.unmount && o.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || K(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			o.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && q(r[i], t, n || typeof e.type != "function");
	n || w(e.__e), e.__c = e.__ = e.__e = void 0;
}
function J(e, t, n) {
	return this.constructor(e, n);
}
function Y(e, t, n) {
	var r, i, s, c;
	t == document && (t = document.documentElement), o.__ && o.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, s = [], c = [], V(t, e = (!r && n || t).__k = T(D, null, [e]), i || y, y, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? a.call(t.childNodes) : null, s, !r && n ? n : i ? i.__e : t.firstChild, r, c), U(s, e, c), e.props.children = null;
}
a = b.slice, o = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, s = 0, O.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = C({}, this.state);
	typeof e == "function" && (e = e(C({}, n), this.props)), e && C(n, e), e != null && this.__v && (t && this._sb.push(t), M(this));
}, O.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), M(this));
}, O.prototype.render = D, c = [], u = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, d = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, N.__r = 0, f = Math.random().toString(8), p = "__d" + f, m = "__a" + f, h = /(PointerCapture)$|Capture$/i, g = 0, _ = B(!1), v = B(!0);
//#endregion
//#region src/api.ts
var ee = class extends Error {
	status;
	constructor(e, t) {
		super(e), this.name = "ApiError", this.status = t;
	}
}, te = (e) => {
	if (!e || typeof e != "object") return "";
	let t = e;
	for (let e of [
		"message",
		"detail",
		"error"
	]) {
		let n = t[e];
		if (typeof n == "string" && n) return n;
	}
	return "";
};
async function ne(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new ee(te(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var re = 0;
Array.isArray;
function X(e, t, n, r, i, a) {
	t ||= {};
	var s, c, l = t;
	if ("ref" in l) for (c in l = {}, t) c == "ref" ? s = t[c] : l[c] = t[c];
	var u = {
		type: e,
		props: l,
		key: n,
		ref: s,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --re,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (s = e.defaultProps)) for (c in s) l[c] === void 0 && (l[c] = s[c]);
	return o.vnode && o.vnode(u), u;
}
//#endregion
//#region src/islands/quality-goals.tsx
var ie = "/api/quality-goals?limit=200", ae = (e, t) => ne(ie, t), oe = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function se({ data: a, error: o, openItem: s, javTitleHtml: c, javDisplayName: l, srcBadge: u }) {
	if (o) return /* @__PURE__ */ X("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: i(o, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = a?.items ?? [];
	return d.length ? /* @__PURE__ */ X("div", {
		class: "qualitylist",
		children: d.map((r) => /* @__PURE__ */ X("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ X("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${l(r)}`,
				onClick: () => s(r.id),
				children: /* @__PURE__ */ X("img", {
					src: oe(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ X("div", { children: [
				/* @__PURE__ */ X("h3", { children: /* @__PURE__ */ X("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => s(r.id),
					dangerouslySetInnerHTML: { __html: c(r) }
				}) }),
				/* @__PURE__ */ X("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ X("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: u(r.location, r.cost) }
						}),
						/* @__PURE__ */ X("span", { children: e[r.location] ?? r.location }),
						/* @__PURE__ */ X("span", { children: t(r.duration) }),
						/* @__PURE__ */ X("span", { children: n(r.size ?? 0) })
					]
				}),
				r.reason ? /* @__PURE__ */ X("p", { children: r.reason }) : null
			] })]
		}, r.id))
	}) : /* @__PURE__ */ X("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/islands.ts
var Z = { "quality-goals": {
	load: ae,
	component: se
} }, ce = () => Object.keys(Z), Q = /* @__PURE__ */ new Map();
async function le(e, t, n, r = {}) {
	let i = Z[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	$(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	Q.set(t, a);
	let o;
	try {
		o = {
			data: await i.load(n, a.controller.signal),
			error: ""
		};
	} catch (e) {
		if (a.controller.signal.aborted) return;
		o = {
			data: null,
			error: e instanceof Error ? e.message : String(e)
		};
	}
	if (Q.get(t) === a) {
		if (r.isCurrent && !r.isCurrent()) {
			Q.delete(t);
			return;
		}
		t.textContent = "", a.painted = !0, Y(T(i.component, {
			...n,
			...o
		}), t);
	}
}
function $(e) {
	let t = Q.get(e);
	t && (t.controller.abort(), Q.delete(e), t.painted && Y(null, e));
}
//#endregion
export { ce as islandNames, le as mountIsland, $ as unmountIsland };
