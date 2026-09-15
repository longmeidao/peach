import { MEDIA_SOURCE_ICONS as e, attachOverlayScrollbar as t, checkboxHtml as n, emptyStateHtml as r, loadingDotsHtml as i, moveGlidePane as a, noteHtml as o, selectFieldHtml as s, selectOptionIconHtml as c, setActionBusy as l, wireCollapse as u, wireSelectField as d } from "/js/ui-components.js";
import { esc as f, icon as p, requestErrorMessage as m } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var h, g, _, v, y, b, x, S, C, w, T, E, D, O, k = {}, A = [], j = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, M = Array.isArray;
function N(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function P(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function F(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? h.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return I(e, o, r, i, null);
}
function I(e, t, n, r, i) {
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
		__v: i ?? ++_,
		__i: -1,
		__u: 0
	};
	return i == null && g.vnode != null && g.vnode(a), a;
}
function L(e) {
	return e.children;
}
function R(e, t) {
	this.props = e, this.context = t;
}
function z(e, t) {
	if (t == null) return e.__ ? z(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? z(e) : null;
}
function ee(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = N({}, t);
		a.__v = t.__v + 1, g.vnode && g.vnode(a), de(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? z(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, pe(r, a, i), t.__e = t.__ = null, a.__e != n && te(a);
	}
}
function te(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), te(e);
}
function ne(e) {
	(!e.__d && (e.__d = !0) && v.push(e) && !re.__r++ || y != g.debounceRendering) && ((y = g.debounceRendering) || b)(re);
}
function re() {
	try {
		for (var e, t = 1; v.length;) v.length > t && v.sort(x), e = v.shift(), t = v.length, ee(e);
	} finally {
		v.length = re.__r = 0;
	}
}
function ie(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || A, v = t.length;
	for (c = ae(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || k, p.__i = d, g = de(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && ge(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = oe(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function ae(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = I(null, o, null, null, null) : M(o) ? o = e.__k[a] = I(L, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = I(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = se(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = z(s)), _e(s, s));
	return r;
}
function oe(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = oe(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = z(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function se(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ce(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || j.test(t) ? n : n + "px";
}
function le(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ce(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ce(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(T, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[w] = r[w] : (n[w] = E, e.addEventListener(t, a ? O : D, a)) : e.removeEventListener(t, a ? O : D, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ue(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[C] == null) t[C] = E++;
			else if (t[C] < n[w]) return;
			return n(g.event ? g.event(t) : t);
		}
	};
}
function de(e, t, n, r, i, a, o, s, c, l) {
	var u, d, f, p, m, h, _, v, y, b, x, S, C, w, T, E, D = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = g.__b) && u(t);
	n: if (typeof D == "function") {
		d = o.length;
		try {
			if (y = t.props, b = D.prototype && D.prototype.render, x = (u = D.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? v = (f = t.__c = n.__c).__ = f.__E : (b ? t.__c = f = new D(y, S) : (t.__c = f = new R(y, S), f.constructor = D, f.render = ve), x && x.sub(f), f.state || (f.state = {}), f.__n = r, p = f.__d = !0, f.__h = [], f._sb = []), b && f.__s == null && (f.__s = f.state), b && D.getDerivedStateFromProps != null && (f.__s == f.state && (f.__s = N({}, f.__s)), N(f.__s, D.getDerivedStateFromProps(y, f.__s))), m = f.props, h = f.state, f.__v = t, p) b && D.getDerivedStateFromProps == null && f.componentWillMount != null && f.componentWillMount(), b && f.componentDidMount != null && f.__h.push(f.componentDidMount);
			else {
				if (b && D.getDerivedStateFromProps == null && y !== m && f.componentWillReceiveProps != null && f.componentWillReceiveProps(y, S), t.__v == n.__v || !f.__e && f.shouldComponentUpdate != null && !1 === f.shouldComponentUpdate(y, f.__s, S)) {
					t.__v != n.__v && (f.props = y, f.state = f.__s, f.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), A.push.apply(f.__h, f._sb), f._sb = [], f.__h.length && o.push(f), s = z(n);
					break n;
				}
				f.componentWillUpdate != null && f.componentWillUpdate(y, f.__s, S), b && f.componentDidUpdate != null && f.__h.push(function() {
					f.componentDidUpdate(m, h, _);
				});
			}
			if (f.context = S, f.props = y, f.__P = e, f.__e = !1, C = g.__r, w = 0, b) f.state = f.__s, f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), A.push.apply(f.__h, f._sb), f._sb = [];
			else do
				f.__d = !1, C && C(t), u = f.render(f.props, f.state, f.context), f.state = f.__s;
			while (f.__d && ++w < 25);
			f.state = f.__s, f.getChildContext != null && (r = N(N({}, r), f.getChildContext())), b && !p && f.getSnapshotBeforeUpdate != null && (_ = f.getSnapshotBeforeUpdate(m, h)), T = u != null && u.type === L && u.key == null ? me(u.props.children) : u, s = ie(e, M(T) ? T : [T], t, n, r, i, a, o, s, c, l), f.base = t.__e, t.__u &= -161, f.__h.length && o.push(f), v && (f.__E = f.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) P(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || fe(t), g.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = he(n.__e, t, n, r, i, a, o, c, l);
	return (u = g.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function fe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(fe));
}
function pe(e, t, n) {
	for (var r = 0; r < n.length; r++) ge(n[r], n[++r], n[++r]);
	g.__c && g.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			g.__e(e, t.__v);
		}
	});
}
function me(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : M(e) ? e.map(me) : e.constructor === void 0 ? N({}, e) : null;
}
function he(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, _, v = n.props || k, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((p = a[l]) && "setAttribute" in p == !!b && (b ? p.localName == b : p.nodeType == 3)) {
			e = p, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (g.__m && g.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && h.call(e.childNodes), !s && a != null) for (v = {}, l = 0; l < e.attributes.length; l++) v[(p = e.attributes[l]).name] = p.value;
		for (l in v) p = v[l], l == "dangerouslySetInnerHTML" ? d = p : l == "children" || l in y || l == "value" && "defaultValue" in y || l == "checked" && "defaultChecked" in y || le(e, l, null, p, i);
		for (l in y) p = y[l], l == "children" ? f = p : l == "dangerouslySetInnerHTML" ? u = p : l == "value" ? m = p : l == "checked" ? _ = p : s && typeof p != "function" || v[l] === p || le(e, l, p, v[l], i);
		if (u) s || d && (u.__html == d.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (d && (e.innerHTML = ""), ie(t.type == "template" ? e.content : e, M(f) ? f : [f], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && z(n, 0), s, c), a != null) for (l = a.length; l--;) P(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && m == null ? e.removeAttribute("value") : m != null && (m !== e[l] || b == "progress" && !m || b == "option" && m != v[l]) && le(e, l, m, v[l], i), l = "checked", _ != null && _ != e[l] && le(e, l, _, v[l], i));
	}
	return e;
}
function ge(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		g.__e(e, n);
	}
}
function _e(e, t, n) {
	var r, i;
	if (g.unmount && g.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || ge(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			g.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && _e(r[i], t, n || typeof e.type != "function");
	n || P(e.__e), e.__c = e.__ = e.__e = void 0;
}
function ve(e, t, n) {
	return this.constructor(e, n);
}
function ye(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), g.__ && g.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], de(t, e = (!r && n || t).__k = F(L, null, [e]), i || k, k, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? h.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), pe(a, e, o), e.props.children = null;
}
h = A.slice, g = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, _ = 0, R.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = N({}, this.state);
	typeof e == "function" && (e = e(N({}, n), this.props)), e && N(n, e), e != null && this.__v && (t && this._sb.push(t), ne(this));
}, R.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ne(this));
}, R.prototype.render = L, v = [], b = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, x = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, re.__r = 0, S = Math.random().toString(8), C = "__d" + S, w = "__a" + S, T = /(PointerCapture)$|Capture$/i, E = 0, D = ue(!1), O = ue(!0);
//#endregion
//#region src/sort-preferences.ts
function be(e, t, n) {
	return e === "seed" ? "" : e === t && n === "asc" ? "asc" : "desc";
}
//#endregion
//#region src/number-setting.ts
var xe = {
	loginDaysSetting: {
		min: 1,
		max: 365,
		unit: "天",
		fallback: 30
	},
	batchSizeSetting: {
		min: 1,
		max: 200,
		unit: "个",
		fallback: 60
	},
	hoverDelaySetting: {
		min: 1,
		max: 60,
		unit: "秒",
		optional: !0,
		fallback: 5
	},
	seekSecondsSetting: {
		min: 1,
		max: 300,
		unit: "秒",
		fallback: 10
	},
	relatedLimitSetting: {
		min: 1,
		max: 60,
		unit: "个",
		optional: !0,
		fallback: 20
	},
	searchHistoryLimitSetting: {
		min: 1,
		max: 50,
		unit: "条",
		optional: !0,
		fallback: 10
	},
	followScheduleSetting: {
		min: 15,
		max: 10080,
		unit: "分钟",
		optional: !0,
		fallback: 60
	}
};
function Se(e, t, n, r) {
	return Number.isInteger(e) && e >= t && e <= n ? e : r;
}
function Ce(e, t, n) {
	let r = e.querySelector("input[type=number]"), i = e.querySelector("[role=switch]"), a = e.querySelector(".board-number-fields");
	r && (r.disabled = n, t !== null && t > 0 && (r.value = String(t))), i && (i.disabled = n, t !== null && (i.checked = t > 0)), a && t !== null && (a.hidden = t === 0);
}
function we(e, t, n, r, i) {
	let a = xe[t];
	if (!a) return !1;
	let { min: o, max: s, unit: c, optional: l, fallback: u } = a, d = `peach.number.${t}`, f = Se(Number(localStorage.getItem(d)), o, s, r > 0 ? r : u), p = document.createElement("div");
	p.className = "board-optional-number";
	let m = document.createElement("div");
	m.className = "board-number-fields", m.hidden = !!l && r === 0;
	let h = document.createElement("div");
	h.className = "board-number-control";
	let g = document.createElement("input");
	g.type = "number", g.className = "geist-input", g.min = String(o), g.max = String(s), g.step = "1", g.value = String(r > 0 ? r : f), g.setAttribute("aria-label", n);
	let _ = document.createElement("span");
	_.textContent = c, _.setAttribute("aria-hidden", "true");
	let v = document.createElement("small");
	v.id = `${t}-error`, v.className = "board-number-error", v.setAttribute("role", "status"), v.hidden = !0, g.setAttribute("aria-describedby", v.id), h.append(g, _), m.append(h, v), p.append(m), e.replaceChildren(p);
	let y = () => {
		g.removeAttribute("aria-invalid"), v.hidden = !0, v.textContent = "";
	}, b = () => {
		if (!g.value || !g.checkValidity()) {
			g.setAttribute("aria-invalid", "true"), v.textContent = `请输入 ${o}–${s} 的整数（${c}）`, v.hidden = !1;
			return;
		}
		y(), f = Number(g.value), localStorage.setItem(d, String(f)), i(g.value);
	};
	if (g.addEventListener("change", b), g.addEventListener("keydown", (e) => {
		e.key === "Enter" && (e.preventDefault(), b());
	}), g.addEventListener("input", () => {
		g.value && g.checkValidity() && y();
	}), l) {
		let e = document.createElement("input");
		e.type = "checkbox", e.className = "ptoggle", e.setAttribute("role", "switch"), e.setAttribute("aria-label", `启用${n}`), e.checked = r > 0, e.onchange = () => {
			y(), m.hidden = !e.checked, e.checked ? (g.value = String(f), b()) : (g.value && g.checkValidity() && (f = Number(g.value)), localStorage.setItem(d, String(f)), i("0"));
		}, p.prepend(e);
	}
	return !0;
}
//#endregion
//#region src/board-metrics.ts
var B = (e) => String(e ?? "").replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Te(e, t, n, r = "chart-no-axes-combined") {
	return `<span class="board-stat-label"><span class="board-stat-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><use href="#i-${/^[a-z0-9-]+$/.test(r) ? r : "database"}"/></svg></span>${B(e)}</span><b class="board-stat-value">${B(t)}</b><small class="board-stat-footer">${B(n || "当前记录")}</small>`;
}
function Ee(e, t, n) {
	if (!Number.isFinite(n) || n <= 0) return "";
	let r = Math.max(0, Math.min(n, Number.isFinite(t) ? t : 0)), i = r / n * 100;
	return `<div class="board-job-progress" role="progressbar" aria-label="${B(e)}" aria-valuemin="0" aria-valuemax="${n}" aria-valuenow="${r}"><svg width="36" height="36" viewBox="0 0 36 36" aria-hidden="true"><circle class="board-job-track" cx="18" cy="18" r="15"/><circle class="board-job-fill" cx="18" cy="18" r="15" pathLength="100" stroke-dasharray="${i} ${100 - i}" transform="rotate(-90 18 18)"/></svg><span>${B(e)}<small>${Math.round(i)}%</small></span></div>`;
}
function De(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0), r = n.reduce((e, t) => e + t.score, 0);
	if (!r) return "";
	let i = 0, a = n.map((e, t) => {
		let n = e.score / r * 100, a = `<circle cx="100" cy="100" r="72" pathLength="100" fill="none" stroke="var(--chart-${t % 4})" stroke-width="22" stroke-dasharray="${n} ${100 - n}" stroke-dashoffset="${-i}"><title>${B(e.name)}：${e.score.toLocaleString()}</title></circle>`;
		return i += n, a;
	}).join("");
	return `<svg class="board-distribution" viewBox="0 0 200 200" role="img" aria-label="${B(t)}"><g transform="rotate(-90 100 100)">${a}</g><text x="100" y="100" text-anchor="middle" dominant-baseline="middle">${B(t)}</text></svg>`;
}
function Oe(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 8);
	if (!n.length) return "";
	let r = n[0].score, i = n.map((e) => `<li><span class="board-rank-fill" style="width:${(e.score / r * 100).toFixed(2)}%"></span><span>${B(e.name)}</span><b>${e.score.toLocaleString()}</b></li>`).join("");
	return `<ol class="board-ranked-chart" aria-label="${B(t)}">${i}</ol>`;
}
function ke(e, t) {
	let n = e.filter((e) => Number.isFinite(e.score) && e.score > 0).slice().sort((e, t) => t.score - e.score).slice(0, 6);
	if (n.length < 3) return "";
	let r = Math.max(...n.map((e) => e.score)), i = n.length, a = (e, t) => {
		let n = e / i * Math.PI * 2 - Math.PI / 2;
		return [160 + Math.cos(n) * t, 140 + Math.sin(n) * t];
	}, o = (e) => n.map((t, n) => a(n, e(n)).map((e) => e.toFixed(2)).join(",")).join(" "), s = [
		25,
		50,
		75,
		100
	].map((e) => `<polygon points="${o(() => e)}" class="board-radar-grid"/>`).join(""), c = n.map((e, t) => {
		let [n, r] = a(t, 116);
		return `<text x="${n}" y="${r}" text-anchor="${n < 145 ? "end" : n > 175 ? "start" : "middle"}">${B(e.name)}</text>`;
	}).join("");
	return `<svg class="board-radar" viewBox="0 0 320 280" role="img" aria-label="${B(t)}"><title>${B(n.map((e) => `${e.name} ${e.score}`).join("，"))}</title>${s}<polygon points="${o((e) => n[e].score / r * 100)}" class="board-radar-value"/>${c}</svg>`;
}
//#endregion
//#region src/board-controls.ts
function Ae(e) {
	let t = Number(e.min) || 0, n = Number(e.max) || 100, r = Number(e.value), i = n > t ? Math.max(0, Math.min(100, (r - t) / (n - t) * 100)) : 0;
	e.style.setProperty("--board-range-value", `${i}%`);
	let a = e.closest(".dual-range");
	if (!a) return;
	let o = e.id === "durMax" ? "max" : "min", s = a.querySelector(`[data-range-end="${o}"]`);
	s || (s = document.createElement("output"), s.className = "board-range-tip", s.dataset.rangeEnd = o, s.setAttribute("aria-hidden", "true"), a.append(s)), s.textContent = r >= n && o === "max" ? "不限" : `${r} 分钟`, s.style.left = `${i}%`, s.style.setProperty("--range-tip-shift", "0px");
	let c = a.getBoundingClientRect(), l = s.getBoundingClientRect(), u = l.right > c.right ? c.right - l.right : l.left < c.left ? c.left - l.left : 0;
	u && s.style.setProperty("--range-tip-shift", `${Math.round(u)}px`), a.querySelectorAll(".board-range-tip").forEach((e) => e.toggleAttribute("data-range-active", e === s));
}
function je() {
	let e = (e) => {
		e.querySelectorAll("input[type=range]").forEach(Ae), Fe(e), Ne(e), Ie(e);
	};
	e(document), new MutationObserver((t) => {
		for (let n of t) for (let t of n.addedNodes) t instanceof Element && (t.matches("input[type=range]") && Ae(t), e(t));
	}).observe(document.body, {
		subtree: !0,
		childList: !0
	}), document.addEventListener("input", (e) => {
		e.target instanceof HTMLInputElement && e.target.type === "range" && Ae(e.target);
	});
	let t = document.createElement("div");
	t.className = "board-tooltip", t.id = "board-control-tooltip", t.role = "tooltip", t.hidden = !0, document.body.append(t);
	let n = null, r = "", i = null, a, o = () => {
		clearTimeout(a), t.hidden = !0, n && (n.hasAttribute("title") || (n.title = r), i === null ? n.removeAttribute("aria-describedby") : n.setAttribute("aria-describedby", i)), n = null;
	}, s = (e, s) => {
		let c = e instanceof Element ? e.closest("[title]") : null;
		!c || c === n || c.closest(".vjs-control") || !c.title.trim() || (o(), n = c, r = c.title, i = c.getAttribute("aria-describedby"), c.removeAttribute("title"), a = setTimeout(() => {
			if (n !== c || !c.isConnected) return;
			t.textContent = r, t.hidden = !1;
			let e = c.getBoundingClientRect(), a = t.getBoundingClientRect();
			t.style.left = `${Math.max(8, Math.min(innerWidth - a.width - 8, e.left + (e.width - a.width) / 2))}px`, t.style.top = `${e.top >= a.height + 16 ? e.top - a.height - 8 : Math.min(innerHeight - a.height - 8, e.bottom + 8)}px`, c.setAttribute("aria-describedby", [i, t.id].filter(Boolean).join(" "));
		}, s));
	};
	document.addEventListener("pointerover", (e) => s(e.target, 400)), document.addEventListener("pointerout", (e) => {
		n && !n.contains(e.relatedTarget) && o();
	}), document.addEventListener("focusin", (e) => s(e.target, 0)), document.addEventListener("focusout", o), document.addEventListener("keydown", (e) => {
		e.key === "Escape" && o();
	}), document.addEventListener("scroll", o, !0), window.addEventListener("resize", o);
}
var Me = /* @__PURE__ */ new Map();
function Ne(e) {
	let t = ".managebar-menu,.board-local-nav:not(.settingscard>.board-local-nav)", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-tabs")) return;
		e.dataset.boardTabs = "true";
		let t = e.className + e.getAttribute("aria-label"), n = (t) => {
			e.style.setProperty("--tab-x", `${t.left}px`), e.style.setProperty("--tab-width", `${t.width}px`);
		}, r = () => {
			let r = e.querySelector("button[aria-selected=true],button[aria-pressed=true]");
			if (!r || !r.offsetWidth) return;
			let i = {
				left: r.offsetLeft,
				width: r.offsetWidth
			};
			n(i), Me.set(t, i);
		}, i = Me.get(t);
		i ? n(i) : r(), requestAnimationFrame(() => {
			e.classList.add("board-tabs-ready"), requestAnimationFrame(r);
		});
		let a = new MutationObserver(r);
		a.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected", "aria-pressed"]
		});
		let o = new ResizeObserver(() => {
			if (!e.isConnected) {
				o.disconnect(), a.disconnect();
				return;
			}
			r();
		});
		o.observe(e);
	});
}
var Pe = /* @__PURE__ */ new Map();
function Fe(e) {
	let t = ".iconswitch,.insightswitch,.insighttabs,.follow-workspace-switch", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-segments") || e.closest("[data-skeleton]")) return;
		e.dataset.boardSegments = "true";
		let t = document.createElement("span");
		t.className = "board-segment-thumb", t.setAttribute("aria-hidden", "true"), e.prepend(t);
		let n = e.className + (e.getAttribute("aria-label") ?? ""), r = Pe.get(n) ?? null, i = () => {
			let i = e.querySelector("label:has(input:checked),button[aria-selected=true]");
			if (!i || !i.offsetWidth) return;
			let o = {
				x: i.offsetLeft,
				y: i.offsetTop,
				w: i.offsetWidth,
				h: i.offsetHeight
			};
			a(t, r, o, "x"), r = o, Pe.set(n, o);
		};
		e.addEventListener("change", i);
		let o = new MutationObserver(i);
		o.observe(e, {
			subtree: !0,
			attributes: !0,
			attributeFilter: ["aria-selected"]
		});
		let s = new ResizeObserver(() => {
			if (!e.isConnected) {
				s.disconnect(), o.disconnect();
				return;
			}
			i();
		});
		s.observe(e), i(), requestAnimationFrame(() => e.classList.add("board-segments-ready"));
	});
}
function Ie(e) {
	let t = ".board-ranked-chart,.board-radar,.tasteranks,.board-heat-card,.board-sankey-card", n = [...e.querySelectorAll(t)];
	e instanceof HTMLElement && e.matches(t) && n.push(e), n.forEach((e) => {
		if (e.hasAttribute("data-board-chart")) return;
		e.dataset.boardChart = "true", e.addEventListener("animationend", () => {
			e.getAnimations?.({ subtree: !0 }).some((e) => e.playState === "running") || e.classList.add("board-chart-settled");
		});
		let t = () => e.classList.add("board-chart-visible");
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) {
			t();
			return;
		}
		let n = new IntersectionObserver((e) => {
			e.some((e) => e.isIntersecting) && (n.disconnect(), t());
		}, { threshold: .15 });
		n.observe(e);
	});
}
function Le(e) {
	e.querySelectorAll(".tasteranks,.insightranking").forEach((e, t) => {
		if (e.children.length <= 5 || e.parentElement?.hasAttribute("data-expandable-ranks")) return;
		let n = document.createElement("div");
		n.className = "board-expand-ranks", n.dataset.expandableRanks = "", e.before(n), n.append(e), e.id = e.id || `board-rank-list-${t}`, e.classList.add("board-rank-list");
		let r = document.createElement("button");
		r.type = "button", r.className = "board-rank-expand", r.setAttribute("aria-controls", e.id), r.setAttribute("aria-expanded", "false"), r.setAttribute("aria-label", "展开更多排名"), r.innerHTML = "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-chevron-down\"/></svg>", n.append(r);
		let i = () => {
			let t = e.children[4];
			e.offsetWidth && (n.style.setProperty("--rank-collapsed-height", `${t.offsetTop - e.offsetTop + t.offsetHeight}px`), n.style.setProperty("--rank-expanded-height", `${e.scrollHeight}px`));
		}, a = () => {
			let t = r.getAttribute("aria-expanded") === "true";
			n.classList.toggle("expanded", t), [...e.children].forEach((e, n) => e.inert = !t && n >= 5), i();
		}, o = (t) => {
			t.target === e && n.classList.remove("toggling");
		};
		e.addEventListener("transitionend", o), e.addEventListener("transitioncancel", o);
		let s = () => {
			let e = r.getBoundingClientRect().top, t = performance.now() + 300, n = () => {
				let i = r.getBoundingClientRect().top - e;
				i && window.scrollBy(0, i), performance.now() < t && requestAnimationFrame(n);
			};
			n();
		};
		r.onclick = () => {
			let e = r.getAttribute("aria-expanded") !== "true";
			r.setAttribute("aria-expanded", String(e)), r.setAttribute("aria-label", e ? "收起排名" : "展开更多排名"), n.classList.add("toggling"), a(), e || s();
		}, new ResizeObserver(i).observe(e), a();
	});
}
//#endregion
//#region node_modules/d3-array/src/max.js
function Re(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n < t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n < i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/min.js
function ze(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n > t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n > i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/sum.js
function Be(e, t) {
	let n = 0;
	if (t === void 0) for (let t of e) (t = +t) && (n += t);
	else {
		let r = -1;
		for (let i of e) (i = +t(i, ++r, e)) && (n += i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-sankey/src/align.js
function Ve(e, t) {
	return e.sourceLinks.length ? e.depth : t - 1;
}
//#endregion
//#region node_modules/d3-sankey/src/constant.js
function He(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-sankey/src/sankey.js
function Ue(e, t) {
	return Ge(e.source, t.source) || e.index - t.index;
}
function We(e, t) {
	return Ge(e.target, t.target) || e.index - t.index;
}
function Ge(e, t) {
	return e.y0 - t.y0;
}
function Ke(e) {
	return e.value;
}
function qe(e) {
	return e.index;
}
function Je(e) {
	return e.nodes;
}
function Ye(e) {
	return e.links;
}
function Xe(e, t) {
	let n = e.get(t);
	if (!n) throw Error("missing: " + t);
	return n;
}
function Ze({ nodes: e }) {
	for (let t of e) {
		let e = t.y0, n = e;
		for (let n of t.sourceLinks) n.y0 = e + n.width / 2, e += n.width;
		for (let e of t.targetLinks) e.y1 = n + e.width / 2, n += e.width;
	}
}
function Qe() {
	let e = 0, t = 0, n = 1, r = 1, i = 24, a = 8, o, s = qe, c = Ve, l, u, d = Je, f = Ye, p = 6;
	function m() {
		let e = {
			nodes: d.apply(null, arguments),
			links: f.apply(null, arguments)
		};
		return h(e), g(e), _(e), v(e), x(e), Ze(e), e;
	}
	m.update = function(e) {
		return Ze(e), e;
	}, m.nodeId = function(e) {
		return arguments.length ? (s = typeof e == "function" ? e : He(e), m) : s;
	}, m.nodeAlign = function(e) {
		return arguments.length ? (c = typeof e == "function" ? e : He(e), m) : c;
	}, m.nodeSort = function(e) {
		return arguments.length ? (l = e, m) : l;
	}, m.nodeWidth = function(e) {
		return arguments.length ? (i = +e, m) : i;
	}, m.nodePadding = function(e) {
		return arguments.length ? (a = o = +e, m) : a;
	}, m.nodes = function(e) {
		return arguments.length ? (d = typeof e == "function" ? e : He(e), m) : d;
	}, m.links = function(e) {
		return arguments.length ? (f = typeof e == "function" ? e : He(e), m) : f;
	}, m.linkSort = function(e) {
		return arguments.length ? (u = e, m) : u;
	}, m.size = function(i) {
		return arguments.length ? (e = t = 0, n = +i[0], r = +i[1], m) : [n - e, r - t];
	}, m.extent = function(i) {
		return arguments.length ? (e = +i[0][0], n = +i[1][0], t = +i[0][1], r = +i[1][1], m) : [[e, t], [n, r]];
	}, m.iterations = function(e) {
		return arguments.length ? (p = +e, m) : p;
	};
	function h({ nodes: e, links: t }) {
		for (let [t, n] of e.entries()) n.index = t, n.sourceLinks = [], n.targetLinks = [];
		let n = new Map(e.map((t, n) => [s(t, n, e), t]));
		for (let [e, r] of t.entries()) {
			r.index = e;
			let { source: t, target: i } = r;
			typeof t != "object" && (t = r.source = Xe(n, t)), typeof i != "object" && (i = r.target = Xe(n, i)), t.sourceLinks.push(r), i.targetLinks.push(r);
		}
		if (u != null) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(u), n.sort(u);
	}
	function g({ nodes: e }) {
		for (let t of e) t.value = t.fixedValue === void 0 ? Math.max(Be(t.sourceLinks, Ke), Be(t.targetLinks, Ke)) : t.fixedValue;
	}
	function _({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.depth = i;
				for (let { target: t } of e.sourceLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function v({ nodes: e }) {
		let t = e.length, n = new Set(e), r = /* @__PURE__ */ new Set(), i = 0;
		for (; n.size;) {
			for (let e of n) {
				e.height = i;
				for (let { source: t } of e.targetLinks) r.add(t);
			}
			if (++i > t) throw Error("circular link");
			n = r, r = /* @__PURE__ */ new Set();
		}
	}
	function y({ nodes: t }) {
		let r = Re(t, (e) => e.depth) + 1, a = (n - e - i) / (r - 1), o = Array(r);
		for (let n of t) {
			let t = Math.max(0, Math.min(r - 1, Math.floor(c.call(null, n, r))));
			n.layer = t, n.x0 = e + t * a, n.x1 = n.x0 + i, o[t] ? o[t].push(n) : o[t] = [n];
		}
		if (l) for (let e of o) e.sort(l);
		return o;
	}
	function b(e) {
		let n = ze(e, (e) => (r - t - (e.length - 1) * o) / Be(e, Ke));
		for (let i of e) {
			let e = t;
			for (let t of i) {
				t.y0 = e, t.y1 = e + t.value * n, e = t.y1 + o;
				for (let e of t.sourceLinks) e.width = e.value * n;
			}
			e = (r - e + o) / (i.length + 1);
			for (let t = 0; t < i.length; ++t) {
				let n = i[t];
				n.y0 += e * (t + 1), n.y1 += e * (t + 1);
			}
			O(i);
		}
	}
	function x(e) {
		let n = y(e);
		o = Math.min(a, (r - t) / (Re(n, (e) => e.length) - 1)), b(n);
		for (let e = 0; e < p; ++e) {
			let t = .99 ** e, r = Math.max(1 - t, (e + 1) / p);
			C(n, t, r), S(n, t, r);
		}
	}
	function S(e, t, n) {
		for (let r = 1, i = e.length; r < i; ++r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { source: t, value: i } of e.targetLinks) {
					let a = i * (e.layer - t.layer);
					n += k(t, e) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(Ge), w(i, n);
		}
	}
	function C(e, t, n) {
		for (let r = e.length - 2; r >= 0; --r) {
			let i = e[r];
			for (let e of i) {
				let n = 0, r = 0;
				for (let { target: t, value: i } of e.sourceLinks) {
					let a = i * (t.layer - e.layer);
					n += A(e, t) * a, r += a;
				}
				if (!(r > 0)) continue;
				let i = (n / r - e.y0) * t;
				e.y0 += i, e.y1 += i, D(e);
			}
			l === void 0 && i.sort(Ge), w(i, n);
		}
	}
	function w(e, n) {
		let i = e.length >> 1, a = e[i];
		E(e, a.y0 - o, i - 1, n), T(e, a.y1 + o, i + 1, n), E(e, r, e.length - 1, n), T(e, t, 0, n);
	}
	function T(e, t, n, r) {
		for (; n < e.length; ++n) {
			let i = e[n], a = (t - i.y0) * r;
			a > 1e-6 && (i.y0 += a, i.y1 += a), t = i.y1 + o;
		}
	}
	function E(e, t, n, r) {
		for (; n >= 0; --n) {
			let i = e[n], a = (i.y1 - t) * r;
			a > 1e-6 && (i.y0 -= a, i.y1 -= a), t = i.y0 - o;
		}
	}
	function D({ sourceLinks: e, targetLinks: t }) {
		if (u === void 0) {
			for (let { source: { sourceLinks: e } } of t) e.sort(We);
			for (let { target: { targetLinks: t } } of e) t.sort(Ue);
		}
	}
	function O(e) {
		if (u === void 0) for (let { sourceLinks: t, targetLinks: n } of e) t.sort(We), n.sort(Ue);
	}
	function k(e, t) {
		let n = e.y0 - (e.sourceLinks.length - 1) * o / 2;
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n += i + o;
		}
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n -= i;
		}
		return n;
	}
	function A(e, t) {
		let n = t.y0 - (t.targetLinks.length - 1) * o / 2;
		for (let { source: r, width: i } of t.targetLinks) {
			if (r === e) break;
			n += i + o;
		}
		for (let { target: r, width: i } of e.sourceLinks) {
			if (r === t) break;
			n -= i;
		}
		return n;
	}
	return m;
}
//#endregion
//#region node_modules/d3-path/src/path.js
var $e = Math.PI, et = 2 * $e, V = 1e-6, tt = et - V;
function nt() {
	this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "";
}
function rt() {
	return new nt();
}
nt.prototype = rt.prototype = {
	constructor: nt,
	moveTo: function(e, t) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t);
	},
	closePath: function() {
		this._x1 !== null && (this._x1 = this._x0, this._y1 = this._y0, this._ += "Z");
	},
	lineTo: function(e, t) {
		this._ += "L" + (this._x1 = +e) + "," + (this._y1 = +t);
	},
	quadraticCurveTo: function(e, t, n, r) {
		this._ += "Q" + +e + "," + +t + "," + (this._x1 = +n) + "," + (this._y1 = +r);
	},
	bezierCurveTo: function(e, t, n, r, i, a) {
		this._ += "C" + +e + "," + +t + "," + +n + "," + +r + "," + (this._x1 = +i) + "," + (this._y1 = +a);
	},
	arcTo: function(e, t, n, r, i) {
		e = +e, t = +t, n = +n, r = +r, i = +i;
		var a = this._x1, o = this._y1, s = n - e, c = r - t, l = a - e, u = o - t, d = l * l + u * u;
		if (i < 0) throw Error("negative radius: " + i);
		if (this._x1 === null) this._ += "M" + (this._x1 = e) + "," + (this._y1 = t);
		else if (d > V) {
			if (!(Math.abs(u * s - c * l) > V) || !i) this._ += "L" + (this._x1 = e) + "," + (this._y1 = t);
			else {
				var f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan(($e - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
				Math.abs(y - 1) > V && (this._ += "L" + (e + y * l) + "," + (t + y * u)), this._ += "A" + i + "," + i + ",0,0," + +(u * f > l * p) + "," + (this._x1 = e + b * s) + "," + (this._y1 = t + b * c);
			}
		}
	},
	arc: function(e, t, n, r, i, a) {
		e = +e, t = +t, n = +n, a = !!a;
		var o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		if (n < 0) throw Error("negative radius: " + n);
		this._x1 === null ? this._ += "M" + c + "," + l : (Math.abs(this._x1 - c) > V || Math.abs(this._y1 - l) > V) && (this._ += "L" + c + "," + l), n && (d < 0 && (d = d % et + et), d > tt ? this._ += "A" + n + "," + n + ",0,1," + u + "," + (e - o) + "," + (t - s) + "A" + n + "," + n + ",0,1," + u + "," + (this._x1 = c) + "," + (this._y1 = l) : d > V && (this._ += "A" + n + "," + n + ",0," + +(d >= $e) + "," + u + "," + (this._x1 = e + n * Math.cos(i)) + "," + (this._y1 = t + n * Math.sin(i))));
	},
	rect: function(e, t, n, r) {
		this._ += "M" + (this._x0 = this._x1 = +e) + "," + (this._y0 = this._y1 = +t) + "h" + +n + "v" + +r + "h" + -n + "Z";
	},
	toString: function() {
		return this._;
	}
};
//#endregion
//#region node_modules/d3-shape/src/constant.js
function it(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function at(e) {
	return e[0];
}
function ot(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/array.js
var st = Array.prototype.slice;
//#endregion
//#region node_modules/d3-shape/src/link/index.js
function ct(e) {
	return e.source;
}
function lt(e) {
	return e.target;
}
function ut(e) {
	var t = ct, n = lt, r = at, i = ot, a = null;
	function o() {
		var o, s = st.call(arguments), c = t.apply(this, s), l = n.apply(this, s);
		if (a ||= o = rt(), e(a, +r.apply(this, (s[0] = c, s)), +i.apply(this, s), +r.apply(this, (s[0] = l, s)), +i.apply(this, s)), o) return a = null, o + "" || null;
	}
	return o.source = function(e) {
		return arguments.length ? (t = e, o) : t;
	}, o.target = function(e) {
		return arguments.length ? (n = e, o) : n;
	}, o.x = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : it(+e), o) : r;
	}, o.y = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : it(+e), o) : i;
	}, o.context = function(e) {
		return arguments.length ? (a = e ?? null, o) : a;
	}, o;
}
function dt(e, t, n, r, i) {
	e.moveTo(t, n), e.bezierCurveTo(t = (t + r) / 2, n, t, i, r, i);
}
function ft() {
	return ut(dt);
}
//#endregion
//#region node_modules/d3-sankey/src/sankeyLinkHorizontal.js
function pt(e) {
	return [e.source.x1, e.y0];
}
function mt(e) {
	return [e.target.x0, e.y1];
}
function ht() {
	return ft().source(pt).target(mt);
}
//#endregion
//#region src/board-sankey.ts
function gt(e = []) {
	let t = e.filter((e) => e.source && e.target && Number.isFinite(e.value) && e.value > 0);
	if (!t.length) return "";
	let n = [...new Set(t.map((e) => e.source))], r = [...new Set(t.map((e) => e.target))], i = Qe().nodeId((e) => e.id).nodeWidth(10).nodePadding(22).extent([[155, 16], [535, 404]])({
		nodes: [...n.map((e) => ({
			id: `source:${e}`,
			name: e,
			side: "source"
		})), ...r.map((e) => ({
			id: `target:${e}`,
			name: e,
			side: "target"
		}))],
		links: t.map((e) => ({
			source: `source:${e.source}`,
			target: `target:${e.target}`,
			value: e.value
		}))
	}), a = t.reduce((e, t) => e + t.value, 0), o = ht(), s = i.links.map((e) => {
		let t = e.source, r = e.target;
		return `<path d="${o(e)}" stroke-width="${Math.max(.5, e.width || 0)}" style="--flow-color:var(--board-chart-${n.indexOf(t.name) % 6})" data-flow-source="${t.index}" data-flow-target="${r.index}" data-flow-value="${e.value}" data-flow-label="${f(t.name)} → ${f(r.name)}" tabindex="0" role="img" aria-label="${f(t.name)} → ${f(r.name)}：${e.value} 条线索"/>`;
	}).join(""), c = i.nodes.map((e) => `<g data-flow-node="${e.index}" data-flow-value="${e.value}" data-flow-label="${f(e.name)}" tabindex="0" role="img" aria-label="${f(e.name)}：${e.value} 条线索"><rect x="${e.x0}" y="${e.y0}" width="10" height="${Math.max(1, (e.y1 || 0) - (e.y0 || 0))}" rx="5" fill="${e.side === "source" ? `var(--board-chart-${n.indexOf(e.name) % 6})` : "var(--color-text-secondary)"}"/><text x="${e.side === "source" ? 145 : 545}" y="${((e.y0 || 0) + (e.y1 || 0)) / 2}" text-anchor="${e.side === "source" ? "end" : "start"}" dominant-baseline="middle">${f(e.name.length > 18 ? e.name.slice(0, 16) + "…" : e.name)}<tspan x="${e.side === "source" ? 145 : 545}" dy="15">${e.side === "source" ? e.value?.toLocaleString() : ((e.value || 0) / a * 100).toFixed(1) + "%"}</tspan></text></g>`).join("");
	return `<section class="board-sankey-card" data-sankey-card><header><h3>创作者线索来源</h3><b data-sankey-number>${a.toLocaleString()}</b><span data-sankey-label>条线索</span></header><div class="board-sankey-scroll"><svg viewBox="0 0 720 435" aria-label="来源网站与创作者线索"><g class="board-sankey-links">${s}</g><g class="board-sankey-nodes">${c}</g></svg></div><footer><span>来源网站</span><span>创作者 · 线索占比</span></footer></section>`;
}
function _t(e) {
	e.querySelectorAll("[data-sankey-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-flow-source]")], n = [...e.querySelectorAll("[data-flow-node]")], r = e.querySelector("[data-sankey-number]"), i = e.querySelector("[data-sankey-label]"), a = r.textContent, o = () => {
			t.forEach((e) => e.style.opacity = ""), n.forEach((e) => e.style.opacity = ""), r.textContent = a, i.textContent = "条线索";
		};
		[...t, ...n].forEach((e) => {
			let a = () => {
				let a = e.dataset.flowNode;
				t.forEach((t) => t.style.opacity = String((a === void 0 ? t === e : t.dataset.flowSource === a || t.dataset.flowTarget === a) ? .7 : .08)), n.forEach((n) => n.style.opacity = String(a === void 0 ? n.dataset.flowNode === e.dataset.flowSource || n.dataset.flowNode === e.dataset.flowTarget ? 1 : .3 : n === e || t.some((e) => e.dataset.flowSource === a && e.dataset.flowTarget === n.dataset.flowNode || e.dataset.flowTarget === a && e.dataset.flowSource === n.dataset.flowNode) ? 1 : .3)), r.textContent = Number(e.dataset.flowValue).toLocaleString(), i.textContent = e.dataset.flowLabel;
			};
			e.addEventListener("pointerenter", a), e.addEventListener("pointerleave", o), e.addEventListener("focus", a), e.addEventListener("blur", o);
		});
	});
}
//#endregion
//#region src/board-analytics.ts
var vt = (e) => Number.isFinite(e) && e >= 0;
function yt(e, t, n = "个视频") {
	let r = e.filter((e) => vt(e.value));
	if (!r.length) return "";
	let i = r.reduce((e, t) => e + t.value, 0), a = Math.max(1, ...r.map((e) => e.value)) * 1.1, o = Math.min(22, 110 / Math.max(1, r.length)), s = Math.min(15, o * .68), c = r.map((e, t) => {
		let r = 32 + t * o, i = e.value / a * 100;
		return `<g style="--ring-color:var(--board-chart-${t % 6});--ring-delay:${t * 60}ms"><circle class="board-ring-track" cx="160" cy="160" r="${r}" stroke-width="${s}"/><circle class="board-ring-value" data-radial-ring="${t}" tabindex="0" role="button" aria-label="${f(e.name)}：${e.value.toLocaleString()} ${f(n)}" aria-pressed="false" cx="160" cy="160" r="${r}" stroke-width="${s}" pathLength="100" stroke-dasharray="${i} ${100 - i}" style="--ring-length:${i}" transform="rotate(-90 160 160)"/></g>`;
	}).join("");
	return `<section class="board-radial-card" data-radial-card data-radial-total="${i}" data-radial-title="${f(t)}"><header><span data-radial-label>${f(t)}</span><b data-radial-number>${i.toLocaleString()}</b><small>${f(n)}</small></header><svg class="board-rings" viewBox="0 0 320 320" aria-label="${f(t)}">${c}</svg><div class="board-radial-tiles">${r.map((e, t) => `<button type="button" data-radial-tile="${t}" data-radial-value="${e.value}" data-radial-name="${f(e.name)}" aria-pressed="false" style="--ring-color:var(--board-chart-${t % 6})"><span><i aria-hidden="true"></i>${f(e.name)}</span><b>${e.value.toLocaleString()}</b>${e.detail ? `<small>${f(e.detail)}</small>` : ""}</button>`).join("")}</div></section>`;
}
function bt(e) {
	e.querySelectorAll("[data-radial-card]").forEach((e) => {
		let t = [...e.querySelectorAll("[data-radial-tile]")], n = [...e.querySelectorAll("[data-radial-ring]")], r = e.querySelector("[data-radial-number]"), i = e.querySelector("[data-radial-label]"), a = -1, o = 0, s = 0, c = (c, l = 300) => {
			e.dataset.radialFocus = String(c), t.forEach((e, t) => {
				e.dataset.active = String(t === c), e.setAttribute("aria-pressed", String(t === a)), n[t]?.setAttribute("aria-pressed", String(t === a)), n[t] && (n[t].dataset.active = String(t === c));
			});
			let u = Number(c < 0 ? e.dataset.radialTotal : t[c]?.dataset.radialValue);
			i.textContent = c < 0 ? e.dataset.radialTitle : t[c].dataset.radialName, cancelAnimationFrame(s);
			let d = o, f = performance.now(), p = (t) => {
				if (!e.isConnected) return;
				let n = matchMedia("(prefers-reduced-motion: reduce)").matches ? 1 : Math.min(1, (t - f) / l);
				o = d + (u - d) * (1 - (1 - n) ** 3), r.textContent = Math.round(o).toLocaleString(), n < 1 && (s = requestAnimationFrame(p));
			};
			s = requestAnimationFrame(p);
		}, l = (e) => {
			a = a === e ? -1 : e, c(a);
		};
		[...t, ...n].forEach((e) => {
			let t = Number(e.getAttribute("data-radial-tile") ?? e.getAttribute("data-radial-ring"));
			e.addEventListener("pointerenter", () => c(t)), e.addEventListener("pointerleave", () => c(a)), e.addEventListener("focus", () => c(t)), e.addEventListener("blur", () => c(a)), e.addEventListener("click", () => l(t)), e instanceof SVGElement && e.addEventListener("keydown", (e) => {
				(e.key === "Enter" || e.key === " ") && (e.preventDefault(), l(t));
			});
		}), e.dataset.radialFocus = "-1", r.textContent = "0";
		let u = () => {
			requestAnimationFrame(() => {
				e.isConnected && (e.classList.add("board-chart-visible"), c(-1, 1200));
			});
		};
		if (typeof IntersectionObserver > "u" || matchMedia("(prefers-reduced-motion: reduce)").matches) u();
		else {
			let t = new IntersectionObserver((e) => {
				e.some((e) => e.isIntersecting) && (t.disconnect(), u());
			}, { threshold: .15 });
			t.observe(e);
		}
	});
}
var xt = [
	"周一",
	"周二",
	"周三",
	"周四",
	"周五",
	"周六",
	"周日"
];
function St(e) {
	if (!e?.days?.length) return "<section class=\"board-activity-empty\"><h3>浏览活跃时间</h3><p>还没有可用于分析的口味网站访问记录。</p></section>";
	let t = Array.from({ length: 7 }, () => Array(24).fill(0));
	for (let n of e.hours || []) Number.isInteger(n.weekday) && n.weekday >= 0 && n.weekday < 7 && Number.isInteger(n.hour) && n.hour >= 0 && n.hour < 24 && vt(n.count) && (t[n.weekday][n.hour] = (t[n.weekday][n.hour] || 0) + n.count);
	let n = Math.max(1, ...t.flat()), r = t.flat().reduce((e, t) => e + t, 0), i = t.map((e, t) => `<span class="board-heat-axis">${xt[t]}</span>${e.map((e, r) => `<button type="button" data-heat-value="${e}" data-heat-label="${xt[t]} ${r}:00" aria-label="${xt[t]} ${r}:00，${e} 次访问" style="--heat:${e ? Math.max(12, e / n * 100) : 0}%"></button>`).join("")}`).join(""), a = e.days.filter((e) => /^\d{4}-\d{2}-\d{2}$/.test(e.date) && vt(e.count)).sort((e, t) => e.date.localeCompare(t.date));
	if (!a.length) return "";
	let o = /* @__PURE__ */ new Date(`${a.at(-1).date}T00:00:00Z`), s = new Date(o);
	s.setUTCDate(s.getUTCDate() - 90);
	let c = new Map(a.map((e) => [e.date, e.count])), l = Math.max(1, ...a.map((e) => e.count)), u = Array.from({ length: 91 }, (e, t) => {
		let n = new Date(s);
		n.setUTCDate(s.getUTCDate() + t);
		let r = n.toISOString().slice(0, 10), i = c.get(r) || 0;
		return `<button type="button" data-heat-value="${i}" data-heat-label="${r}" aria-label="${r}，${i} 次访问" style="--heat:${i ? Math.max(12, i / l * 100) : 0}%"></button>`;
	}).join("");
	return `<div class="board-activity-charts"><section class="board-heat-card" data-heat-card><header><h3>浏览活跃时间</h3><b data-heat-number>${r.toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-heat-scroll"><div class="board-hour-grid"><span></span>${Array.from({ length: 24 }, (e, t) => `<span class="board-heat-axis">${t % 2 ? "" : t}</span>`).join("")}${i}</div></div><footer>星期 × 小时<span>${f(e.timezone || "UTC+08:00")}</span></footer></section><section class="board-heat-card" data-heat-card><header><h3>每日活跃</h3><b data-heat-number>${a.filter((e) => e.date >= s.toISOString().slice(0, 10)).reduce((e, t) => e + t.count, 0).toLocaleString()}</b><span data-heat-title data-heat-default="口味网站访问">口味网站访问</span></header><div class="board-day-grid">${u}</div><footer>${s.toISOString().slice(0, 10)}<span>${a.at(-1).date}</span></footer></section></div>`;
}
function Ct(e) {
	e.querySelectorAll("[data-heat-card]").forEach((e) => {
		let t = e.querySelector("[data-heat-number]"), n = e.querySelector("[data-heat-title]"), r = t.textContent;
		e.querySelectorAll("[data-heat-value]").forEach((e) => {
			let i = () => {
				t.textContent = Number(e.dataset.heatValue).toLocaleString(), n.textContent = e.dataset.heatLabel;
			}, a = () => {
				t.textContent = r, n.textContent = n.dataset.heatDefault;
			};
			e.addEventListener("pointerenter", i), e.addEventListener("pointerleave", a), e.addEventListener("focus", i), e.addEventListener("blur", a);
		});
	});
}
//#endregion
//#region src/sidebar-groups.ts
var wt = (e) => e.replace(/[&<>"']/g, (e) => ({
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;",
	"'": "&#39;"
})[e]);
function Tt(e, t, n = "", r = "") {
	if (!t) return "";
	let i = `sidebar-group-${encodeURIComponent(e)}`;
	return `<details class="sec${r ? " cat-" + wt(r) : ""}" data-sidebar-group="${wt(e)}"><summary role="button" class="board-section-toggle"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"/></svg><span>${wt(e)}</span></summary><div class="board-sidebar-body" id="${i}">${t}${n}</div></details>`;
}
function Et(e) {
	e.querySelectorAll("[data-sidebar-group]").forEach((e) => {
		if (e.dataset.sidebarWired) return;
		e.dataset.sidebarWired = "true";
		let t = e.querySelector(".board-sidebar-body"), n = `peach.sidebar.group.${e.dataset.sidebarGroup}`, r = null;
		try {
			r = sessionStorage.getItem(n);
		} catch {}
		let i = !!t.querySelector("[aria-pressed=true]");
		e.open = r === null ? i : r === "open";
	}), u(e, "details[data-sidebar-group]", "sidebar-collapse"), e.querySelectorAll(".board-section-toggle").forEach((e) => {
		e.dataset.persistWired || (e.dataset.persistWired = "true", e.addEventListener("click", () => {
			let t = `peach.sidebar.group.${e.closest("[data-sidebar-group]").dataset.sidebarGroup}`;
			try {
				sessionStorage.setItem(t, e.getAttribute("aria-expanded") === "true" ? "open" : "closed");
			} catch {}
		}));
	});
}
var Dt = !1;
async function Ot(e, t) {
	if (Dt) return;
	if (!document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches) {
		t();
		return;
	}
	let n = e.getBoundingClientRect(), r = n.left + n.width / 2, i = n.top + n.height / 2, a = Math.hypot(Math.max(r, innerWidth - r), Math.max(i, innerHeight - i)) * 2.5, o = document.createElement("style");
	o.textContent = `::view-transition-old(root){animation:none}::view-transition-new(root){mix-blend-mode:normal;mask-image:radial-gradient(circle closest-side,#000 78%,#0006 88%,transparent);mask-repeat:no-repeat;will-change:mask-position,mask-size;animation:peach-theme-reveal 560ms cubic-bezier(.16,1,.3,1) both}@keyframes peach-theme-reveal{from{mask-position:${r}px ${i}px;mask-size:0px 0px}to{mask-position:${r - a / 2}px ${i - a / 2}px;mask-size:${a}px ${a}px}}`, Dt = !0, document.head.append(o);
	let s = document.documentElement;
	s.dataset.themeSnapshot = "true";
	let c = !1, l = () => {
		c || (c = !0, t());
	};
	try {
		await document.startViewTransition(l).finished;
	} catch {
		l();
	} finally {
		delete s.dataset.themeSnapshot, o.remove(), Dt = !1;
	}
}
//#endregion
//#region src/api.ts
var kt = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(m(e, t)), this.name = "ApiError", this.status = t, this.body = n;
	}
}, At = (e) => {
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
}, jt = (e) => m(e);
async function Mt(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new kt(At(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function Nt(e, t, n = "POST", r) {
	let i = await fetch(e, {
		method: n,
		...r ? { signal: r } : {},
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json"
		},
		credentials: "same-origin",
		body: JSON.stringify(t)
	}), a = null;
	try {
		a = await i.json();
	} catch {}
	if (!i.ok) throw new kt(At(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region src/configuration-endpoints.ts
var Pt = "/api/configuration", H, U, Ft, It, Lt = 0, Rt = [], W = g, zt = W.__b, Bt = W.__r, Vt = W.diffed, Ht = W.__c, Ut = W.unmount, Wt = W.__;
function Gt(e, t) {
	W.__h && W.__h(U, e, Lt || t), Lt = 0;
	var n = U.__H || (U.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function G(e) {
	return Lt = 1, Kt(tn, e);
}
function Kt(e, t, n) {
	var r = Gt(H++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : tn(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = U, !U.__f)) {
		var i = function(e, t, n) {
			if (!r.__c.__H) return !0;
			var i = !1, o = r.__c.props !== e;
			if (r.__c.__H.__.some(function(e) {
				if (e.__N) {
					i = !0;
					var t = e.__[0];
					e.__ = e.__N, e.__N = void 0, t !== e.__[0] && (o = !0);
				}
			}), a) {
				var s = a.call(this, e, t, n);
				return i ? s || o : s;
			}
			return !i || o;
		};
		U.__f = !0;
		var a = U.shouldComponentUpdate, o = U.componentWillUpdate;
		U.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, U.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function qt(e, t) {
	var n = Gt(H++, 3);
	!W.__s && en(n.__H, t) && (n.__ = e, n.u = t, U.__H.__h.push(n));
}
function K(e) {
	return Lt = 5, Jt(function() {
		return { current: e };
	}, []);
}
function Jt(e, t) {
	var n = Gt(H++, 7);
	return en(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Yt() {
	for (var e; e = Rt.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Qt), t.__h.some($t), t.__h = [];
		} catch (n) {
			t.__h = [], W.__e(n, e.__v);
		}
	}
}
W.__b = function(e) {
	U = null, zt && zt(e);
}, W.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Wt && Wt(e, t);
}, W.__r = function(e) {
	Bt && Bt(e), H = 0;
	var t = (U = e.__c).__H;
	t && (Ft === U ? (t.__h = [], U.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Qt), t.__h.some($t), t.__h = [], H = 0)), Ft = U;
}, W.diffed = function(e) {
	Vt && Vt(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Rt.push(t) !== 1 && It === W.requestAnimationFrame || ((It = W.requestAnimationFrame) || Zt)(Yt)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ft = U = null;
}, W.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Qt), e.__h = e.__h.filter(function(e) {
				return !e.__ || $t(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], W.__e(n, e.__v);
		}
	}), Ht && Ht(e, t);
}, W.unmount = function(e) {
	Ut && Ut(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Qt(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && W.__e(t, n.__v));
};
var Xt = typeof requestAnimationFrame == "function";
function Zt(e) {
	var t, n = function() {
		clearTimeout(r), Xt && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Xt && (t = requestAnimationFrame(n));
}
function Qt(e) {
	var t = U, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), U = t;
}
function $t(e) {
	var t = U;
	e.__c = e.__(), U = t;
}
function en(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function tn(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var nn = 0;
Array.isArray;
function q(e, t, n, r, i, a) {
	t ||= {};
	var o, s, c = t;
	if ("ref" in c) for (s in c = {}, t) s == "ref" ? o = t[s] : c[s] = t[s];
	var l = {
		type: e,
		props: c,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --nn,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return g.vnode && g.vnode(l), l;
}
//#endregion
//#region src/react-slot.tsx
function rn({ mount: e, props: t }) {
	let n = K(null), r = K(null), i = K(t);
	i.current = t;
	let [a, o] = G("");
	return qt(() => {
		let t = !1;
		return import("/dist/peach-react.js").then((a) => {
			if (t || !n.current) return;
			let o = a[e];
			r.current = o(n.current, i.current);
		}, (e) => {
			t || o(e instanceof Error ? e.message : String(e));
		}), () => {
			t = !0, r.current?.unmount(), r.current = null;
		};
	}, [e]), qt(() => {
		r.current?.update(t);
	}), a ? /* @__PURE__ */ q("p", {
		class: "configbad",
		role: "alert",
		children: ["界面组件没有加载：", a]
	}) : /* @__PURE__ */ q("div", {
		ref: n,
		class: "peach-react"
	});
}
//#endregion
//#region src/islands/configuration.tsx
var an = (e, t) => Mt(Pt, t);
function on({ receipt: e, data: t, error: n }) {
	if (n || !t) return /* @__PURE__ */ q("div", {
		class: "configpage",
		dangerouslySetInnerHTML: { __html: o(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		}) }
	});
	let r = {
		data: t,
		receipt: e
	};
	return /* @__PURE__ */ q("div", {
		class: "configpage",
		children: [
			t.startup ? /* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "通用"
			}) : null,
			t.startup ? /* @__PURE__ */ q(rn, {
				mount: "mountGeneralSettings",
				props: r
			}) : null,
			/* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "媒体"
			}),
			/* @__PURE__ */ q(rn, {
				mount: "mountMediaSettings",
				props: r
			}),
			t.peach_proxy || t.access ? /* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "网络与访问"
			}) : null,
			t.peach_proxy || t.access ? /* @__PURE__ */ q(rn, {
				mount: "mountNetworkSettings",
				props: r
			}) : null,
			/* @__PURE__ */ q("h2", {
				class: "configgroup",
				children: "更新与维护"
			}),
			/* @__PURE__ */ q(rn, {
				mount: "mountMaintenanceSettings",
				props: r
			})
		]
	});
}
//#endregion
//#region src/jobs.ts
function sn(e, t = 0, n = 0) {
	return n > 0 ? Ee(e, t, n) : i(e);
}
async function cn(e) {
	let t = e.pause || ((e) => new Promise((t) => setTimeout(t, e))), n = 0;
	for (; e.active();) {
		let r;
		try {
			r = await e.read(AbortSignal.timeout(15e3));
		} catch (r) {
			if (!e.active()) return;
			n++, e.disconnected(r), await t(Math.min(2e3 * 2 ** Math.min(n, 4), 3e4));
			continue;
		}
		if (!e.active() || (n = 0, e.render(r), e.once) || !e.keepWatching && r.status !== "running") return;
		await t(2e3);
	}
}
function ln(e) {
	let t = e.note || ((e) => o(e, {
		label: "任务状态",
		variant: "error"
	})), n = e.loading || i, r = e.progress || ((e, t, n) => sn(n || `已处理 ${e} / ${t}`, e, t)), a = e.container || ((e) => `<section class="followtask" data-geist-fieldset aria-label="任务进度"><div class="geist-fieldset-content">${e}</div></section>`), s = document.createElement("div");
	e.host.hidden = !0, s.dataset.followJob = "", s.setAttribute("aria-live", "polite"), e.host.prepend(s);
	let c = e.storageKey || "peach-follow-job", l = sessionStorage.getItem(c) || void 0, u = !1;
	cn({
		read: e.read,
		active: () => !u && e.active() && s.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (i) => {
			let o = i.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				l = i.job_id, l && sessionStorage.setItem(c, l);
				let t = i.current, o = (t?.attempt || 1) > 1 ? ` · 第 ${t?.attempt}/${t?.max_attempts} 次尝试${t?.retry_in ? `，${t.retry_in} 秒后重试` : ""}` : "", u = (i.message || (e.title ? e.title + (i.total ? `：已完成 ${i.checked || 0}/${i.total}` : "") : "") || (i.total ? `${i.older ? "抓取历史" : "检查更新"}：已完成 ${i.checked || 0}/${i.total} 个来源` : "正在准备检查任务…")) + (t ? ` · ${t.label || t.provider || ""}${o}` : ""), d = (i.total || 0) > 0 ? r(i.checked || 0, i.total, u) : n(u);
				s.innerHTML = a(d);
			} else if (l && l === i.job_id) l = void 0, u = !0, e.host.hidden = i.status !== "failed", sessionStorage.removeItem(c), s.innerHTML = i.status === "failed" ? t(i.error || "检查失败") : "", e.complete(i);
			else {
				if (l && i.status === "idle") {
					e.host.hidden = !1, s.innerHTML = t("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(c), u = !0;
					return;
				}
				s.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, s.innerHTML = t("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/review-evidence.ts
var un = (e = "") => /^https?:\/\//i.test(e) ? e : "";
function dn(e = "") {
	let t = un(e) || (e.startsWith("/") && !e.startsWith("//") ? e : "");
	return `<div class="reviewimage" data-review-picture><span class="reviewimageempty"${t ? " hidden" : ""}>未取得来源图片</span>${t ? `<img src="${f(t)}" alt="来源候选图片" loading="lazy">` : ""}</div>`;
}
function fn(e) {
	let t = un(e.profile_url), n = (e.preview_assets || []).slice(0, 6), r = Math.max(0, Number(e.video_count || e.videos || 0));
	return `<section class="reviewidentityevidence"><h5>候选身份：${f(e.babepedia_name || "未标注")}</h5>
    <div class="reviewevidenceactions">${t ? `<a class="geist-button externallink" href="${f(t)}" target="_blank" rel="noopener noreferrer">来源资料<svg class="externalmark" viewBox="0 0 24 24" aria-hidden="true"><use href="#i-external-link" /></svg></a>` : ""}
    <button type="button" class="geist-button" data-entity-kind="creator" data-entity-name="${f(e.creator || "")}">查看全部 ${r.toLocaleString()} 部作品</button></div>
    ${dn(e.preview_url)}
    <p>通过后记录身份判断。</p>
    ${n.length ? `<h5>本地作品样本</h5><div class="reviewevidencesamples">${n.map((e) => `<div class="reviewevidencesample">
      <button class="geist-button" type="button" data-review-open-item="${e.id}"><span data-middle-truncate title="${f(e.name)}">${f(e.name)}</span></button>
      <button class="geist-button" type="button" data-review-reveal="${e.id}" aria-label="打开 ${f(e.name)} 的文件位置">文件位置</button>
    </div>`).join("")}</div>` : "<p>暂无本地作品样本，打开全部作品核对。</p>"}</section>`;
}
function pn(e) {
	for (let t of e.querySelectorAll("[data-review-picture] img")) {
		let e = () => {
			t.hidden = !0;
			let e = t.parentElement?.querySelector(".reviewimageempty");
			e && (e.hidden = !1);
		};
		t.addEventListener("error", e), t.complete && !t.naturalWidth && e();
	}
}
//#endregion
//#region src/selection.ts
function mn(e, t, n, r, i, a = i || !e.has(r)) {
	let o = n === null ? -1 : t.indexOf(n), s = t.indexOf(r);
	return i && o >= 0 && s >= 0 ? t.slice(Math.min(o, s), Math.max(o, s) + 1).forEach((t) => e.add(t)) : a ? e.add(r) : e.delete(r), r;
}
function hn(e, t) {
	let n = t.filter((t) => e.has(t)).length;
	return {
		count: n,
		all: n > 0 && n === t.length,
		mixed: n > 0 && n < t.length
	};
}
function gn(e, t, n) {
	t.forEach((t) => n ? e.add(t) : e.delete(t));
}
function _n({ count: e, label: t, all: n, summary: r, actions: i, locked: a = !1 }) {
	e && (e.textContent = t), n && (n.checked = r.all, n.indeterminate = r.mixed);
	for (let e of i) e.disabled = !r.count || a;
}
//#endregion
//#region src/review-bulk.ts
var vn = () => ({
	busy: !1,
	category: "",
	filter: "",
	groupBy: "candidates",
	anchor: null,
	selected: /* @__PURE__ */ new Set(),
	choices: /* @__PURE__ */ new Map(),
	assets: /* @__PURE__ */ new Map(),
	errors: /* @__PURE__ */ new Map()
});
function yn(e) {
	let t = e?.querySelector(".reviewbulktoolbar");
	if (!e || e.classList.contains("review-skeleton") || !t || t.offsetParent === null) return;
	e.style.setProperty("--review-controls-height", `${t.getBoundingClientRect().height}px`);
	let n = [t, ...e.querySelectorAll(".reviewgroupbar")];
	for (let e of n) {
		let t = parseFloat(getComputedStyle(e).top);
		e.classList.toggle("is-stuck", e.offsetParent !== null && window.scrollY > 0 && Number.isFinite(t) && Math.abs(e.getBoundingClientRect().top - t) <= 1);
	}
	let r = n.filter((e) => e.classList.contains("is-stuck"));
	e.classList.toggle("review-is-stuck", r.length > 0);
	let i = t, a = n.slice(1).find((e) => e.offsetParent !== null && Math.abs(e.getBoundingClientRect().top - t.getBoundingClientRect().bottom) <= 2) || t;
	e.classList.add("review-has-pane"), n.forEach((e) => e.classList.toggle("review-pane-member", e === i || e === a));
	let o = i.getBoundingClientRect(), s = a.getBoundingClientRect();
	e.style.setProperty("--review-pane-top", `${o.top}px`), e.style.setProperty("--review-pane-left", `${o.left}px`), e.style.setProperty("--review-pane-width", `${o.width}px`), e.style.setProperty("--review-pane-height", `${s.bottom - o.top}px`);
}
function bn(e, t) {
	let n = [[
		"candidates",
		t ? "按候选数量" : "全部待复核",
		"list-filter"
	]];
	return e.some((e) => e.source || e.candidates?.some((e) => e.source)) && n.push([
		"source",
		"按来源",
		"list-filter"
	]), e.some((e) => e.field) && n.push([
		"field",
		"按字段",
		"list-filter"
	]), n;
}
function xn(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r of e) {
		let e, i;
		if (t === "field") e = r.field || "__unspecified_field", i = r.field_label || r.field || "未标注字段";
		else if (t === "source") {
			let t = [...new Set((r.candidates?.map((e) => e.source || "") || [r.source || ""]).filter(Boolean))].sort();
			e = JSON.stringify(t), i = t.join(" / ") || "未标注来源";
		} else e = r.candidates ? r.candidates.length === 1 ? "single" : "multiple" : "pending", i = e === "single" ? "单一候选" : e === "multiple" ? "需选择来源" : "待复核";
		n.has(e) || n.set(e, {
			key: e,
			title: i,
			rows: []
		}), n.get(e).rows.push(r);
	}
	return [...n.values()];
}
function Sn(e, t, n, r, i) {
	e.anchor = mn(e.selected, t, e.anchor, n, r, i);
}
async function Cn(e, t, n, r) {
	let i = [], a = 0;
	for (let o of e) {
		if (!r()) break;
		try {
			let e = await t(o.payload);
			if (!e.ok) throw Error(e.error || "服务端未采用该项");
			a++, n(o.key);
		} catch (e) {
			i.push({
				key: o.key,
				message: jt(e)
			});
		}
	}
	return {
		completed: a,
		failures: i
	};
}
function wn(e) {
	return e.length ? [...new Set(e.flatMap((e) => e.candidates?.map((e) => e.source || "") || []))].filter((t) => t && e.every((e) => e.candidates?.filter((e) => e.source === t).length === 1)) : [];
}
function Tn(e, t) {
	let r = e.querySelector(".reviewlist");
	if (!r || !t.rows.length || t.locked) return;
	let i = t.state, a = [...r.querySelectorAll("[data-review-key]")];
	t.category !== void 0 && i.category !== t.category && (i.category = t.category, i.filter = "", i.groupBy = "candidates", i.anchor = null);
	let o = t.catalog || t.rows, c = bn(o, t.metadata);
	c.some((e) => e[0] === i.groupBy) || (i.groupBy = "candidates", i.filter = "");
	let u = xn(o, i.groupBy);
	u.some((e) => e.key === i.filter) || (i.filter = "");
	let f = () => [...r.querySelectorAll("[data-review-key]")].filter((e) => !e.closest("[hidden]")), m = () => f().filter((e) => i.selected.has(e.dataset.reviewKey)), h = () => t.rows.filter((e) => m().some((t) => t.dataset.reviewKey === e.item_key)), g = (e) => !e.querySelector("[data-review-status=\"approved\"]")?.disabled, _ = (e, t = "") => {
		let n = document.createElement("button");
		return n.type = "button", n.className = `geist-button ${t}`.trim(), n.textContent = e, n;
	}, v = document.createElement("div");
	v.className = "reviewbulkbar reviewbulktoolbar", v.setAttribute("role", "group"), v.setAttribute("aria-label", "复核批量操作");
	let y = document.createElement("div");
	y.className = "reviewgroupby", y.innerHTML = s(c, i.groupBy, { label: "筛选分组方式" });
	let b = d(y.firstElementChild);
	y.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), b.addEventListener("change", () => {
		if (i.busy || !c.some((e) => e[0] === b.value)) return;
		i.groupBy = b.value, i.filter = "", i.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewgroupby button")?.focus({ preventScroll: !0 });
	});
	let x = document.createElement("div");
	x.className = "reviewcategoryfilter", x.hidden = u.length < 2, x.innerHTML = s([[
		"",
		"全部分类",
		"list-filter"
	], ...u.map((e) => [
		e.key,
		`${e.title} · ${e.rows.length}`,
		"list-filter"
	])], i.filter, { label: i.groupBy === "field" ? "筛选字段分类" : "筛选当前分类" });
	let S = x.querySelector("[data-select-menu]");
	if (S) {
		let e = document.createElement("div");
		e.setAttribute("role", "group"), e.setAttribute("aria-label", i.groupBy === "field" ? "字段分类" : "当前分类");
		let t = document.createElement("div");
		t.className = "reviewfilterheading", t.textContent = e.getAttribute("aria-label"), t.setAttribute("aria-hidden", "true"), e.append(t, ...Array.from(S.children).slice(1)), S.append(e);
	}
	let C = d(x.firstElementChild);
	x.querySelectorAll("[data-select-option] .gselectmark").forEach((e) => e.remove()), C.addEventListener("change", () => {
		if (i.busy || C.value && !u.some((e) => e.key === C.value)) return;
		i.filter = C.value, i.anchor = null;
		let n = e.parentElement;
		t.refresh(), n?.querySelector(".reviewcategoryfilter button")?.focus({ preventScroll: !0 });
	});
	let w = _("全选本页"), T = _("通过所选", "primary"), E = _("拒绝所选", "error"), D = document.createElement("span");
	D.className = "reviewselectedcount selectiondockcount", D.setAttribute("role", "status");
	let O = document.createElement("div");
	O.className = "reviewbulksource", O.hidden = !t.metadata;
	let k = document.createElement("p");
	k.className = "reviewstate reviewbulkfeedback", k.setAttribute("role", "status");
	let A = document.createElement("div");
	A.className = "reviewbulkdecisions", A.append(T, E);
	let j = document.createElement("div");
	j.className = "selectiondock reviewdock", j.setAttribute("role", "group"), j.setAttribute("aria-label", "复核所选项目");
	let M = _("取消选择");
	j.append(D, O, A, M, k), v.append(y, x, w);
	let N = e.querySelector(".reviewcontrols");
	N ? N.after(v) : r.before(v), e.append(j), r.classList.add("reviewgroups");
	let P = () => {
		i.selected.clear(), i.anchor = null, L();
	};
	M.onclick = () => {
		i.busy || (P(), w.focus({ preventScroll: !0 }));
	}, w.onclick = () => {
		if (i.busy) return;
		let e = f(), t = m().length === e.length;
		e.forEach((e) => t ? i.selected.delete(e.dataset.reviewKey) : i.selected.add(e.dataset.reviewKey)), L();
	}, T.onclick = () => R("approved", T), E.onclick = () => R("rejected", E);
	let F = [];
	for (let e of u) {
		let t = e.rows.map((e) => a.find((t) => t.dataset.reviewKey === e.item_key)).filter((e) => !!e);
		if (!t.length) continue;
		let o = document.createElement("section");
		o.className = "reviewgroup", o.hidden = !!i.filter && e.key !== i.filter;
		let s = document.createElement("div");
		s.className = "reviewbulkbar reviewgroupbar";
		let c = document.createElement("h3");
		c.textContent = `${e.title} · ${t.length}`;
		let l = _("全选本组"), u = document.createElement("div");
		u.className = "reviewlist", s.append(c, l), o.append(s, u), r.append(o), l.onclick = () => {
			if (i.busy) return;
			let e = t.map((e) => e.dataset.reviewKey);
			gn(i.selected, e, !e.every((e) => i.selected.has(e))), L();
		}, F.push(() => {
			let e = t.every((e) => i.selected.has(e.dataset.reviewKey));
			l.innerHTML = p(e ? "check-check-outline" : "check-check") + (e ? "清空本组" : "全选本组"), l.setAttribute("aria-pressed", String(e));
		});
		for (let e of t) {
			u.append(e);
			let t = e.dataset.reviewKey;
			i.errors.has(t) && (e.querySelector(".reviewstate").textContent = i.errors.get(t));
			let r = e.querySelector("h4,.reviewentity b") || e, a = document.createElement("label");
			a.className = "reviewpickitem", a.innerHTML = n();
			let o = a.querySelector("input");
			if (o.setAttribute("aria-label", `选择 ${e.querySelector("legend")?.textContent || r.textContent || t}`), r !== e) {
				let e = document.createElement("span");
				e.className = "reviewpickname", e.append(...r.childNodes), r.classList.add("reviewpickheading"), r.append(a, e);
			} else e.prepend(a);
			let s = (e, n) => {
				Sn(i, f().map((e) => e.dataset.reviewKey), t, e, n), L();
			};
			if (a.addEventListener("mousedown", (e) => {
				e.shiftKey && e.preventDefault();
			}), a.addEventListener("click", (e) => {
				e.target !== o && (e.preventDefault(), i.busy || (o.focus(), s(e.shiftKey, !o.checked)));
			}), o.addEventListener("click", (e) => {
				i.busy || s(e.shiftKey, o.checked);
			}), o.addEventListener("keydown", (n) => {
				if (!(i.busy || !n.shiftKey)) {
					if (n.key === " ") n.preventDefault(), s(!0, !0);
					else if (n.key === "ArrowDown" || n.key === "ArrowUp") {
						n.preventDefault();
						let r = f(), a = r[r.indexOf(e) + (n.key === "ArrowDown" ? 1 : -1)];
						a && (i.anchor === null && (i.anchor = t), Sn(i, r.map((e) => e.dataset.reviewKey), a.dataset.reviewKey, !0, !0), L(), a.querySelector(".reviewpickitem input")?.focus());
					}
				}
			}), F.push(() => {
				o.checked = i.selected.has(t);
			}), i.assets.has(t)) {
				let n = i.assets.get(t), r = [...e.querySelectorAll("[data-review-asset]")];
				r.forEach((e) => {
					let t = n.includes(Number(e.dataset.reviewAsset));
					e.setAttribute("aria-pressed", String(t)), e.classList.toggle("picked", t);
				});
				let a = e.querySelector("[data-picked-count]");
				a && (a.textContent = `已选 ${n.length} / ${r.length}`);
			}
			e.addEventListener("click", (n) => {
				n.target.closest("[data-review-asset],[data-pick-all],[data-pick-none]") && i.assets.set(t, [...e.querySelectorAll("[data-review-asset][aria-pressed=\"true\"]")].map((e) => Number(e.dataset.reviewAsset)));
			});
			for (let n of e.querySelectorAll("input[type=\"radio\"]")) i.choices.has(t) && (n.checked = i.choices.get(t) === n.value), n.addEventListener("change", () => {
				n.checked && i.choices.set(t, n.value), L();
			});
		}
	}
	e.addEventListener("keydown", (t) => {
		i.busy || !e.contains(r) || (t.key === "Escape" && i.selected.size && (t.preventDefault(), t.stopPropagation(), P()), (t.ctrlKey || t.metaKey) && t.key.toLowerCase() === "a" && !t.target.matches("textarea,input:not([type=\"checkbox\"]):not([type=\"radio\"])") && (t.preventDefault(), t.stopPropagation(), f().forEach((e) => i.selected.add(e.dataset.reviewKey)), L()));
	});
	let I = "";
	function L() {
		let e = m(), n = e.length > 0 && e.length === f().length;
		w.innerHTML = p(n ? "check-check-outline" : "check-check") + (n ? "清空当前选择" : i.filter ? "全选当前分类" : "全选本页"), w.setAttribute("aria-pressed", String(n)), j.hidden = !e.length, _n({
			count: D,
			label: `已选 ${e.length} 项`,
			summary: hn(i.selected, f().map((e) => e.dataset.reviewKey)),
			actions: [T, E]
		}), T.disabled ||= e.some((e) => !g(e));
		let r = wn(h());
		O.hidden = !t.metadata || !h().some((e) => (e.candidates?.length || 0) > 1);
		let a = e.length && !r.length ? "所选项目无共同来源" : "统一选择来源", o = JSON.stringify([a, r]);
		if (o !== I) {
			I = o, O.innerHTML = s([["", a], ...r.map((e) => [e, e])], "", { label: "统一选择来源" });
			let e = d(O.firstElementChild);
			e.disabled = !r.length, e.addEventListener("change", () => {
				if (!(i.busy || !wn(h()).includes(e.value))) {
					for (let n of m()) {
						let r = t.rows.find((e) => e.item_key === n.dataset.reviewKey).candidates.find((t) => t.source === e.value);
						n.querySelectorAll("input[type=\"radio\"]").forEach((e) => {
							e.checked = e.value === r.candidate_key;
						}), i.choices.set(n.dataset.reviewKey, r.candidate_key);
					}
					k.textContent = `已选择 ${e.value}，点击通过所选采用。`;
				}
			});
		}
		F.forEach((e) => e());
	}
	async function R(n, r) {
		if (i.busy || !m().length) return;
		let a = m().map((e) => ({
			key: e.dataset.reviewKey,
			payload: {
				...t.payload(e),
				status: n
			}
		}));
		if (n === "approved" && t.metadata && a.some((e) => !e.payload.candidate_key)) {
			k.textContent = "请先为所选的多来源候选选择来源。", m().find((e) => !e.querySelector("input[type=\"radio\"]:checked"))?.querySelector("input[type=\"radio\"]")?.focus();
			return;
		}
		i.busy = !0, k.textContent = `正在处理 0 / ${a.length}`, l(r, !0);
		let o = [...e.querySelectorAll("button,input")], s = o.map((e) => e.getAttribute("aria-disabled"));
		o.forEach((e) => e.setAttribute("aria-disabled", "true"));
		let c = (e) => {
			e instanceof KeyboardEvent && e.key === "Tab" || (e.preventDefault(), e.stopImmediatePropagation());
		};
		e.addEventListener("click", c, !0), e.addEventListener("keydown", c, !0);
		let u = 0, d = await Cn(a, async (e) => {
			try {
				return await t.submit(e);
			} finally {
				u++, t.active() && (k.textContent = `正在处理 ${u} / ${a.length}`);
			}
		}, (e) => {
			i.selected.delete(e), i.errors.delete(e), t.applied(e);
		}, t.active);
		if (i.busy = !1, e.removeEventListener("click", c, !0), e.removeEventListener("keydown", c, !0), o.forEach((e, t) => {
			let n = s[t];
			n === null ? e.removeAttribute("aria-disabled") : e.setAttribute("aria-disabled", n);
		}), l(r, !1), !t.active()) return;
		t.notify(`已${n === "approved" ? "通过" : "拒绝"} ${d.completed} 项${d.failures.length ? `，${d.failures.length} 项未完成` : ""}`), d.failures.forEach((e) => i.errors.set(e.key, e.message));
		let f = e.parentElement;
		t.refresh(), f?.querySelector(".reviewbulktoolbar button")?.focus({ preventScroll: !0 });
	}
	L(), yn(e);
}
function En(e, t, n = 1) {
	let r = (e, t) => Array.from({ length: t - e + 1 }, (t, n) => e + n);
	if (n * 2 + 5 >= t) return r(1, t);
	let i = Math.max(e - n, 1), a = Math.min(e + n, t), o = i > 2, s = a < t - 2;
	return !o && s ? [
		...r(1, 3 + 2 * n),
		"…",
		t
	] : o && !s ? [
		1,
		"…",
		...r(t - (2 + 2 * n), t)
	] : [
		1,
		"…",
		...r(i, a),
		"…",
		t
	];
}
function Dn(e, t) {
	return Math.max(1, Math.ceil(e / t));
}
function On(e, t) {
	return Math.min(Math.max(1, Math.floor(e) || 1), t);
}
function kn(e, t, n) {
	if (t <= 1) return "";
	let r = En(e, t).map((t) => t === "…" ? "<li class=\"board-page-dots\" aria-hidden=\"true\">…</li>" : `<li><button type="button" class="board-page" data-page="${t}" aria-label="第 ${t} 页"${t === e ? " aria-current=\"page\"" : ""}>${t}</button></li>`).join("");
	return `<nav class="board-pagination" aria-label="${n}">
    <button type="button" class="geist-button" data-page="${e - 1}"${e <= 1 ? " disabled" : ""}><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-left"></use></svg>上一页</button>
    <ul>${r}</ul>
    <button type="button" class="geist-button" data-page="${e + 1}"${e >= t ? " disabled" : ""}>下一页<svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg></button>
  </nav>`;
}
//#endregion
//#region src/native-image.ts
function An(e, t, n, r) {
	return e > 0 && t > 0 && e === n && t === r;
}
function jn(e, t, n, r, i = 1) {
	let a = Number.isFinite(i) && i > 0 ? i : 1;
	e /= a, t /= a;
	let o = [
		e,
		t,
		n,
		r
	].every((e) => Number.isFinite(e) && e > 0), s = o && Math.min(n, r) >= 64 && (e < n * .4 || t < r * .4), c = o ? Math.min(1, n / e, r / t) : 1;
	return {
		small: s,
		width: e * c,
		height: t * c
	};
}
//#endregion
//#region src/avatar-picker.tsx
var Mn = {
	gfriends: "图库",
	history: "用过的"
};
function Nn({ kind: e, id: n, name: r, onPicked: i }) {
	let a = K(null), o = K(null), s = K(null), [c, l] = G(null), [u, d] = G(""), [f, p] = G(""), [m, h] = G(""), [g, _] = G(!1);
	qt(() => {
		if (!g || c) return;
		let t = new AbortController();
		return Mt(`/api/avatar-choices?kind=${e}&id=${n}`, t.signal).then(l).catch((e) => {
			t.signal.aborted || d(jt(e));
		}), () => t.abort();
	}, [
		g,
		c,
		e,
		n
	]), qt(() => {
		t(o.current);
	}, [g, c]);
	let v = () => {
		_(!0), a.current?.showModal();
	}, y = () => {
		_(!1), a.current?.close();
	}, b = async (e, t) => {
		p(t), d("");
		try {
			await e(), y(), l(null), i();
		} catch (e) {
			d(jt(e));
		} finally {
			p("");
		}
	}, x = (t) => b(() => Nt("/api/avatar-pick", {
		kind: e,
		id: n,
		ref: t.ref
	}), t.ref), S = () => b(() => Nt("/api/avatar-pick", {
		kind: e,
		id: n,
		url: m.trim()
	}), "url"), C = async (t) => b(async () => {
		let r = await fetch(`/api/avatar-pick?kind=${e}&id=${n}&name=${encodeURIComponent(t.name)}`, {
			method: "POST",
			credentials: "same-origin",
			body: t
		});
		if (!r.ok) {
			let e = await r.json().catch(() => null);
			throw Error(e?.error || `请求失败（${r.status}）`);
		}
	}, "file"), w = c?.choices || [], T = (c?.matched_names || []).filter((e) => e !== r), E = c ? T.length ? `${r}：图库里按「${T.join("」「")}」找到的。` : w.length ? `${r}：换上的那张留在本机，随时能换回来。` : `${r}：图库里没有这个名字，用下面两种方式换。` : "正在找可用的图…", D = !!c && c.index_stale && !w.some((e) => e.source === "gfriends");
	return /* @__PURE__ */ q("div", {
		class: "avatarpick",
		children: [/* @__PURE__ */ q("button", {
			type: "button",
			class: "avatarpick-open",
			onClick: v,
			"aria-haspopup": "dialog",
			"aria-label": `更换${r}的头像`,
			title: "更换头像",
			children: /* @__PURE__ */ q("svg", {
				viewBox: "0 0 24 24",
				"aria-hidden": "true",
				children: /* @__PURE__ */ q("use", { href: "#i-plus" })
			})
		}), /* @__PURE__ */ q("dialog", {
			ref: a,
			class: "geist-modal avatarpick-popover",
			"aria-label": "更换头像",
			onCancel: y,
			onClick: (e) => {
				e.target === a.current && y();
			},
			children: [/* @__PURE__ */ q("div", {
				class: "avatarpick-head",
				children: [
					/* @__PURE__ */ q("span", {
						class: "avatarpick-mark",
						"aria-hidden": "true",
						children: /* @__PURE__ */ q("svg", {
							viewBox: "0 0 24 24",
							children: /* @__PURE__ */ q("use", { href: "#i-user-round" })
						})
					}),
					/* @__PURE__ */ q("div", {
						class: "avatarpick-headtext",
						children: [
							/* @__PURE__ */ q("div", {
								class: "avatarpick-title",
								children: [/* @__PURE__ */ q("h3", { children: "更换头像" }), !!w.length && /* @__PURE__ */ q("span", {
									class: "geist-badge",
									children: [w.length, " 张可选"]
								})]
							}),
							/* @__PURE__ */ q("p", { children: E }),
							D && /* @__PURE__ */ q("p", {
								class: "avatarpick-note",
								children: "图库索引还没取过，只能从用过的图里选。"
							}),
							u && /* @__PURE__ */ q("p", {
								class: "avatarpick-error",
								role: "alert",
								children: u
							})
						]
					}),
					/* @__PURE__ */ q("button", {
						type: "button",
						class: "avatarpick-close",
						onClick: y,
						"aria-label": "关闭",
						children: /* @__PURE__ */ q("svg", {
							viewBox: "0 0 24 24",
							"aria-hidden": "true",
							children: /* @__PURE__ */ q("use", { href: "#i-x" })
						})
					})
				]
			}), /* @__PURE__ */ q("div", {
				class: "avatarpick-panel",
				children: [/* @__PURE__ */ q("div", {
					class: "avatarpick-gridwrap",
					children: /* @__PURE__ */ q("div", {
						class: "avatarpick-grid",
						role: "listbox",
						"aria-label": "候选头像",
						ref: o,
						children: w.map((t) => /* @__PURE__ */ q("button", {
							type: "button",
							role: "option",
							"aria-selected": t.current,
							disabled: !!f,
							class: `avatarpick-cell${t.current ? " current" : ""}`,
							title: `${Mn[t.source] || t.source} · ${t.label}` + (t.width ? ` · ${t.width}×${t.height}` : "") + (t.found_by ? ` · 按「${t.found_by}」找到` : ""),
							onClick: () => x(t),
							children: [
								/* @__PURE__ */ q("img", {
									loading: "lazy",
									alt: "",
									src: `/avatar-choice?kind=${e}&id=${n}&ref=${encodeURIComponent(t.ref)}`
								}),
								/* @__PURE__ */ q("span", { children: t.label }),
								t.current && /* @__PURE__ */ q("b", { children: "在用" })
							]
						}, t.ref))
					})
				}), /* @__PURE__ */ q("div", {
					class: "avatarpick-actions",
					children: [
						/* @__PURE__ */ q("button", {
							type: "button",
							class: "geist-button",
							disabled: !!f,
							onClick: () => s.current?.click(),
							children: "从本机选图片"
						}),
						/* @__PURE__ */ q("input", {
							ref: s,
							type: "file",
							accept: "image/png,image/jpeg",
							hidden: !0,
							onChange: (e) => {
								let t = e.currentTarget.files?.[0];
								e.currentTarget.value = "", t && C(t);
							}
						}),
						/* @__PURE__ */ q("div", {
							class: "avatarpick-url",
							children: [/* @__PURE__ */ q("input", {
								type: "url",
								class: "geist-input",
								value: m,
								placeholder: "https://…",
								"aria-label": "图片地址",
								onInput: (e) => h(e.currentTarget.value)
							}), /* @__PURE__ */ q("button", {
								type: "button",
								class: "geist-button",
								disabled: !m.trim() || !!f,
								onClick: S,
								children: "用这个地址"
							})]
						})
					]
				})]
			})]
		})]
	});
}
function Pn(e, t) {
	ye(/* @__PURE__ */ q(Nn, { ...t }), e);
}
function Fn(e) {
	ye(null, e);
}
//#endregion
//#region src/entity-skeleton.ts
function In(e, t, n) {
	return `<section data-skeleton="entity/${e}" role="status" aria-label="正在读取资料">
    <span class="sr-only">正在读取资料</span><div aria-hidden="true">
    <section class="entityhero"><div class="entityprofile"><div class="entityportrait ${e === "studio" || e === "agency" ? "square " : ""}skeleton"></div>
      <div class="entityidentity entityskeletontext"><div class="entitytitle"><h2 class="skeleton">&nbsp;</h2></div>
      <div class="alias"><span class="skeleton"></span></div>
      <div class="entitylinks"><span class="skeleton"></span></div></div></div></section>
    <div class="board-filter-frame" data-filter-frame>
      <section class="entitytagbar" data-filter-row="top"><div class="filterscroll" data-skeleton-tier="pill"></div></section>
      ${t}</div>
    <div class="entitysection">${n}</div></div></section>`;
}
//#endregion
//#region src/board-skeleton.ts
var J = (e = "60%") => `<span class="skeleton" style="width:${e}"></span>`, Y = () => `${J("80%")}${J("48%")}`, X = (e, t) => e.repeat(t), Ln = (e, t = "metricstrip") => `<div class="${t}">${e.map((e) => `<div class="tastesummary"><span class="board-stat-label">${e}</span><b class="board-stat-value">${J("45%")}</b><small class="board-stat-footer">${J("60%")}</small></div>`).join("")}</div>`, Rn = (e, t = "skeleton-tabs") => `<div class="${t}">${e.map((e) => `<span>${e}</span>`).join("")}</div>`, zn = (e, t) => `<div class="${t} skeleton-segments" data-board-segments="true">${e.map((e, t) => `<span${t === 0 ? " class=\"skeleton-segment-selected\"" : ""}>${e}</span>`).join("")}</div>`, Bn = (e) => `<section class="board-radial-card"><header><span>${e}</span><b>${J()}</b></header><div class="board-rings skeleton-rings"><span class="skeleton skeleton-ring"></span></div><div class="skeleton-lines">${Y()}</div></section>`, Z = (e) => `<section class="insightpanel"><header>${e}</header><div class="insightpanelbody skeleton-lines">${X(Y(), 3)}</div></section>`, Vn = (e) => `<button class="fbtn" type="button" disabled>${e}</button>`, Hn = (e) => `<div class="fsechead" data-collapse-toolbar><h3>关注列表</h3><span class="fmeta">${J("100px")}</span><div class="followtoolbaractions"><button class="fbtn primary followcheckall" disabled>${p("refresh-cw")}<span data-collapse-label>检查全部</span></button><div class="iconswitch" data-board-segments="true"><label>${p("layout-grid")}</label><label>${p("table")}</label></div><span class="fmanagesort" data-collapse-field>${p("sort")}${s([["checked", "检查时间"]], "checked", {
	label: "关注列表排序",
	attr: "disabled"
})}</span><button class="fbtn fmanagedir" disabled>${p("arrow-down")}</button>${e ? "" : Vn(p("chevron-up") + "<span data-collapse-label>全部收起</span>")}</div></div>`, Un = () => `<div class="fsource frow"><span class="fchannelcheck">${J("18px")}</span><b>${J("85%")}</b><span class="fprovider">${J("54px")}</span><span class="fmeta fchecked">${J("40px")}</span><span class="fsourceactions"><span class="skeleton skeleton-icon"></span><span class="skeleton skeleton-icon"></span></span></div>`, Wn = () => `<details class="fauthor" open><summary class="fauthorhead"><span class="favatar skeleton"></span><b>${J("90px")}</b><span class="skeleton skeleton-icon"></span><span class="fmeta">${J("40px")}</span><span class="board-author-actions"><button type="button" class="fbtn small" data-follow-author-select disabled>${p("check-check")}<span data-author-select-label>全选</span></button><span class="skeleton skeleton-icon"></span></span></summary><div class="fauthorsources">${X(Un(), 3)}</div></details>`;
function Gn() {
	return `<div data-skeleton="detail" role="status" aria-label="正在读取作品详情"><div class="sgrid" aria-hidden="true"><div class="vwrap skeleton-detail-media skeleton"></div><aside class="side"><div class="sidecontent skeleton-lines">${J("85%")}${J("65%")}${X(Y(), 4)}</div></aside></div></div>`;
}
function Kn(e, t = {}) {
	let r = "";
	if (e === "/stats") r = `<div class="insightpage statsdashboard"><header class="insighttoolbar">${J("38%")}</header>${Ln([
		"馆藏视频",
		"看过",
		"内容标签",
		"使用空间"
	])}<section class="insightdetail"><div class="insightdetailbody"><div class="board-inventory-charts">${Bn("网盘与本地")}${Bn("媒体库")}</div></div></section>${Z("内容标签")}</div>`;
	else if (e === "/taste") r = `<div class="tastepage"><header class="tastehead">${zn(["浏览器记录", "Peach 内部"], "insightswitch")}${J("24%")}</header><div class="tastestate"></div>${Ln([
		"浏览记录",
		"口味维度",
		"浏览候选",
		"私有导出"
	], "tastesummaries")}<section class="tastehero"><div class="insightcopy"><span>浏览器画像</span><div class="skeleton skeleton-radar"></div></div><div class="tastebars skeleton-lines">${X(Y(), 4)}</div></section>${Z("口味分析")}<div class="board-activity-charts">${Z("浏览活动")}${Z("时间分布")}</div>${Z("标签")}</div>`;
	else if (e === "/follow-manage") {
		let e = t.followLayout === "table", i = e ? `<div class="ftableframe"><div class="ftablewrap"><table class="ftable"><thead><tr>${[
			"选择",
			"创作者",
			"来源",
			"站点",
			"状态",
			"上次检查",
			"操作"
		].map((e) => `<th>${e === "选择" ? "<label>" + n("disabled aria-label=\"全选本页来源\"") + "</label>" : e}</th>`).join("")}</tr></thead><tbody>${X(`<tr>${[
			"20px",
			"90px",
			"120px",
			"60px",
			"40px",
			"100px",
			"60px"
		].map((e) => `<td>${J(e)}</td>`).join("")}</tr>`, 6)}</tbody></table></div></div>` : `<div class="board-follow-list">${X(Wn(), 4)}</div>`;
		r = `<div class="follow followmanage"><div class="fmanageoverview">${[
			"关注创作者",
			"启用来源",
			"检查失败",
			"未看更新"
		].map((e) => `<div><span>${e}</span><b>${J()}</b></div>`).join("")}</div>${zn([
			"关注列表",
			"添加关注",
			"来源和凭证"
		], "follow-workspace-switch")}<div class="fmain"><section class="fsec" data-follow-workspace-panel="list">${Hn(e)}<div class="board-follow-selection"${e ? " hidden" : ""}><label>${n("disabled")}全选本页</label></div><div class="frows fsources" data-layout="${e ? "table" : "default"}">${i}<div class="followpagefooter"><div class="followpageinfo">${J("120px")}${J("100px")}</div></div></div></section></div></div>`;
	} else if (e === "/configuration") r = `<div class="configpage">${Rn([
		"通用",
		"媒体",
		"网络与访问",
		"更新与维护"
	])}<section class="configfieldset"><div class="geist-fieldset-content"><h3 class="geist-fieldset-title">开机自启</h3><div class="skeleton-lines">${X(`<div class="skeleton-setting">${J("35%")}<span class="skeleton skeleton-toggle"></span></div>`, 3)}</div></div><footer class="geist-fieldset-footer">${J("100px")}</footer></section></div>`;
	else if (e === "/activity") r = `<div class="activitypage">${[
		"正在进行",
		"被挡下的",
		"最近完成"
	].map((e) => `<section class="activitysection"><h3 class="geist-fieldset-title">${e}</h3><div class="activity-runs"><article class="cleanupfieldset activity-run"><div class="geist-fieldset-content skeleton-lines">${J("35%")}${Y()}</div></article></div></section>`).join("")}</div>`;
	else if (e === "/duplicates") r = `<div class="review"><div class="collection-summary">${J("38%")}</div><div class="fsechead dupactions"><h3>批量保留</h3>${J("40%")}</div>${X(`<section class="dupgroup"><div class="duphead">${J("45%")}</div><div class="duplist">${X(`<div class="duprow"><span class="dupcover skeleton"></span><span class="dupmarks">${J()}</span><span class="dupname">${J("90%")}</span>${J()}${J()}${J()}<span class="duppath">${J("70%")}</span></div>`, 2)}</div></section>`, 2)}</div>`;
	else if (e === "/quality-goals") r = `<div class="quality-workspace"><div class="collection-summary"><strong>待升级</strong>${J("20%")}</div><div class="qualitylist">${X(`<article class="qualityitem"><span class="qualitycover skeleton"></span><div class="qualitybody skeleton-lines">${Y()}</div><footer class="qualityactions">${J("80%")}</footer></article>`, 6)}</div></div>`;
	else if (e === "/playlists") r = `<section class="playlistpage"><header><div><h2>播放列表</h2><p>保存 Mix，按自己的顺序继续播放。</p></div><div class="playlistcreate skeleton-lines"><span>新播放列表</span>${J("200px")}</div></header><div class="playlistcards">${X(`<article class="card playlistcard"><div class="mixstack"><div class="pic skeleton"></div></div><div class="mixmeta"><span class="mav skeleton"></span><div class="mixcopy skeleton-lines">${Y()}</div></div></article>`, 6)}</div></section>`;
	else return "";
	return `<div class="board-page-skeleton" data-skeleton="board${e}" role="status" aria-label="正在读取页面"><div aria-hidden="true" inert>${r}</div></div>`;
}
//#endregion
//#region src/catalog-onboarding.ts
var qn = [
	"loc",
	"creator",
	"performer",
	"studio",
	"series",
	"agency",
	"tag",
	"tag_match",
	"len",
	"dur_min",
	"dur_max",
	"orient",
	"region",
	"state",
	"jav",
	"thumb"
];
function Jn() {
	let e = (e) => Array(64).fill(e).join("");
	return {
		tiers: "<div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"av\"><span class=\"ring\"></span><span class=\"nm\">&nbsp;</span></span>") + "</div><div class=\"tier catalog-placeholder\" aria-hidden=\"true\">" + e("<span class=\"brandpill\"><span class=\"mk\"></span><span class=\"placeholder-name\">&nbsp;</span></span>") + "</div>",
		tags: "<span class=\"catalog-placeholder placeholder-tags\" aria-hidden=\"true\">" + e("<span class=\"pill\">&nbsp;</span>") + "</span>"
	};
}
async function Yn(e, t) {
	let n = new URLSearchParams();
	for (let t of qn) e[t] && n.set(t, e[t]);
	let [r, i] = await Promise.all([t("/api/facets?" + n), t("/api/items?" + n + "&limit=5")]), a = [...new Set([
		...r.creators || [],
		...r.tagperformers || [],
		...r.tags || []
	].map((e) => String(e.k || "")).concat((i.items || []).map((e) => e.code || e.name || "")))].filter((e) => e.length > 1).slice(0, 10);
	return (await Promise.all(a.map(async (e) => {
		let r = new URLSearchParams(n);
		return r.set("q", e), r.set("limit", "1"), (await t("/api/items?" + r)).total > 0 ? e : "";
	}))).filter(Boolean);
}
function Xn({ kind: e = "catalog", filtered: t = !1, jav: n = !1, configurable: i = !1, online: a = !1 } = {}) {
	let o = i ? "<button class=\"geist-button primary\" data-empty-settings>添加内容</button>" : "", s = "<a class=\"geist-button" + (!i || a ? " primary" : "") + "\" href=\"/follow-manage?tab=add\">添加关注</a>";
	if (t || n) return r("search", n ? "还没有符合条件的 JAV 作品" : "没有符合条件的内容", n ? "已扫描但尚未补充发行资料的视频可在全部内容中查看。" : "清除筛选或搜索条件后查看全部内容。", { actions: "<a class=\"geist-button primary\" href=\"/?loc=&thumb=0\">查看全部内容</a>" });
	if (e !== "catalog") {
		let t = (a ? {
			tags: "标签",
			performers: "创作者"
		}[e] : "") || {
			tags: "标签",
			performers: "艺人",
			creators: "创作者",
			studios: "厂牌",
			agencies: "事务所",
			series: "系列"
		}[e] || "资料";
		return r(e === "tags" ? "tags" : "user-round", "还没有" + t, a ? "添加关注来源并获取内容后，这里会显示来源上的" + t + "。" : "添加内容并补充资料后，这里会显示对应信息。", { actions: a ? s : o + s });
	}
	return r("play", "还没有视频", "添加媒体文件夹或关注来源，开始建立你的馆藏。", { actions: o + s });
}
//#endregion
//#region src/sidebar.ts
function Zn(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Qn(e, t) {
	return e.dataset.surface?.split("?")[0] === t.split("?")[0] && e.querySelector(".dnav") ? (e.dataset.surface = t, !1) : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function $n(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/management.ts
function er(e) {
	return e.filter((e) => ["115", "pikpak"].includes(e.location) && (e.roots === void 0 || e.roots.length > 0)).map((e) => e.location);
}
function tr(e, t) {
	return t.filter((t) => e.some((e) => e.location === t));
}
function nr() {
	let e = [
		["人工复核", "square-check-big"],
		["高清版", "sparkles"],
		["重复文件", "file-stack"],
		["垃圾文件", "file-archive"],
		["回收站", "trash"]
	], t = "<span class=\"skeleton cleanup-count-skeleton\" aria-hidden=\"true\"></span>";
	return `<div class="cleanuppage" data-skeleton="cleanup" aria-busy="true" aria-label="正在读取数据管理状态">
    <div class="cleanupstats">${e.map(([e, n]) => `
      <button type="button" class="board-plain-stat" disabled>
        <span class="board-plain-stat-head"><span class="board-stat-tile"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-${n}"></use></svg></span>${e}</span>
        <strong>${t}</strong><span class="cleanupmeta">${t}</span></button>`).join("")}</div>
    <div class="cleanupgrid">
      <section class="cleanupfieldset board-processing-skeleton" data-geist-fieldset aria-labelledby="cleanup-loading-scan">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-scan">扫描与采集</h3>
          <p>扫描媒体文件夹，导入已有资料，采集缺失信息。</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><a class="board-link-button" href="/scraping"><span>来源和凭证</span><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-arrow-up"></use></svg></a><div class="splitbutton board-button-group primary"><button type="button" class="splitmain geist-button primary" disabled><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-database"></use></svg>扫描并补全资料</button><button type="button" class="splittoggle geist-button primary" disabled aria-label="更多扫描与采集方式"><svg aria-hidden="true"><use href="#i-chevron-down"></use></svg></button></div></footer>
      </section>
      <section class="cleanupfieldset cleanupemptyfolders" data-geist-fieldset aria-labelledby="cleanup-loading-empty">
        <div class="geist-fieldset-content"><h3 class="geist-fieldset-title" id="cleanup-loading-empty">空文件夹</h3>
          <strong>${t}</strong><p class="cleanupmeta">${t}</p></div>
        <footer class="geist-fieldset-footer" data-geist-fieldset-footer><button type="button" disabled><svg aria-hidden="true"><use href="#i-scan-search"></use></svg><span>扫描空文件夹</span></button></footer>
      </section></div>
    <section class="resourcesync" aria-labelledby="cleanup-loading-links">
      <h2 id="cleanup-loading-links">链接管理</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">站外链接</h3>
          <div class="linksummary"><div class="linkstats">${[
		"链接总数",
		"官网/事务所",
		"社交账号",
		"作品资料站",
		"资料出处"
	].map((e) => `<div><span>${e}</span><b>${t}</b></div>`).join("")}</div></div></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查死链</button></div>
      </div></section>
    <section class="resourcesync" aria-labelledby="cleanup-loading-sync">
      <h2 id="cleanup-loading-sync">资源同步</h2>
      <div class="resourcesyncbox" data-geist-fieldset>
        <div class="resourcesyncbody geist-fieldset-content"><h3 class="geist-fieldset-title">文件与记录核对</h3>
          <p>${t}</p></div>
        <div class="resourcesyncfooter geist-fieldset-footer" data-geist-fieldset-footer><button class="resourceaction primary" type="button" disabled>检查文件</button></div>
      </div></section></div>`;
}
function rr(e, t = !1, n = !1) {
	if (t || n) return "";
	let r = "<svg class=\"externalmark\" viewBox=\"0 0 24 24\" aria-hidden=\"true\"><use href=\"#i-external-link\"></use></svg>";
	return `<details class="taste-history-guide"${e ? " open" : ""}>
    <summary><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#i-chevron-right"></use></svg>浏览器历史记录导入指南</summary>
    <div class="taste-history-guide-content">
      <p>在运行 Peach 的电脑上使用浏览器：点击上方「读取 Peach 主机」。</p>
      <p>记录在其他设备上：导出文件后，点击上方「导入历史」。多台设备的文件分别导入。</p>
      <ul><li>Chrome：在 <a class="externallink" href="https://takeout.google.com/" target="_blank" rel="noreferrer">Google Takeout${r}</a> 选择 Chrome 历史记录，下载 ZIP 后直接导入。</li>
      <li>其他浏览器：使用 <a class="externallink" href="https://github.com/purarue/browserexport" target="_blank" rel="noreferrer">browserexport${r}</a> 导出历史记录，再导入导出文件。</li></ul>
      <p>需要刷新时再次读取或导入；数据源可在页面底部移除。</p>
      <button type="button" class="geist-button taste-guide-skip">跳过</button>
    </div></details>`;
}
var ir = "peach-taste-guide-dismissed";
function ar(e, t) {
	u(e, ".taste-history-guide", "taste-guide-collapse");
	let n = e.querySelector(".taste-history-guide");
	n?.querySelector(".taste-guide-skip")?.addEventListener("click", () => {
		t.setItem(ir, "1"), n.remove();
	});
}
//#endregion
//#region src/resource-sync.ts
var Q = (e = 0) => Number(e).toLocaleString(), or = {
	local: "本地磁盘",
	115: "115",
	pikpak: "PikPak"
}, sr = (t) => c(e[t] ?? "database"), cr = (e, t, n) => `<article class="board-plain-stat resourcestat">
    <span class="board-plain-stat-head">${e}</span>
    <strong>${t}</strong>
    <span class="cleanupmeta">${n}</span></article>`;
function lr(e, t) {
	let n = e.cache || {
		files: 0,
		bytes: 0
	}, r = !!(e.missing || n.files);
	return `<div class="cleanupstats resourcestats">${(e.sources || []).map((e) => cr(`<span class="board-stat-tile resourcestat-tile">${sr(e.location)}</span>${or[e.location] || "媒体来源"}<span class="resourcestat-state ${e.online ? "online" : "offline"}">${e.online ? "可访问" : "离线，已跳过"}</span>`, e.online ? `${Q(e.missing)} 项` : "—", [e.online ? `找不到文件 · 已检查 ${Q(e.checked)} 项` : `馆藏中有 ${Q(e.total)} 项`, e.unreadable ? `${Q(e.unreadable)} 项读取失败，已跳过` : ""].filter(Boolean).join(" · "))).join("")}
    ${cr("待移入回收站", `${Q(e.missing)} 项`, "")}
    ${cr("可清理的缓存", `${Q(n.files)} 个`, n.files ? t(n.bytes) : "")}</div>
    ${r ? o(`将把找不到文件的 ${Q(e.missing)} 项馆藏记录移入回收站，并清理 ${Q(n.files)} 个闲置缓存。`, { label: "清理内容" }) : ""}
    <div class="resourceapplyrow geist-fieldset-footer" data-geist-fieldset-footer>${r ? "<button class=\"geist-button primary\" type=\"button\" id=\"resourceApply\">清理失效记录与缓存</button>" : "<p class=\"resourcesyncok\">已检查可访问的来源，没有待清理的记录或缓存。</p>"}</div>`;
}
//#endregion
//#region src/jav-artwork.ts
function ur(e) {
	return [
		"small",
		"sleeve",
		"preview"
	].includes(String(e)) ? "small" : "big";
}
function dr(e) {
	return {
		javLayout: ur(e.javLayout),
		javImage: fr(e.javLayout === "preview" ? "thumbnail" : e.javImage)
	};
}
function fr(e) {
	return e === "thumbnail" ? "thumbnail" : "cover";
}
function pr(e, t) {
	return e.is_jav && e.code && e.has_cover && (fr(t) === "cover" || !e.has_thumb) ? "cover" : e.has_thumb ? "thumbnail" : "";
}
function mr(e, t) {
	let n = Number(e?.px?.[0]), r = Number(e?.px?.[1]), i = Number(e?.x0);
	if (!(n > 0 && r > 0 && t > 0) || !Number.isFinite(i)) return null;
	let a = Math.min(1, Math.max(0, i / n)), o = n / r / t, s = (1 - a) * o;
	if (!(s > 0)) return null;
	let c = s <= 1 ? (1 - s) / 2 - a * o : 1 - o, l = (e) => Math.round(e * 1e4) / 100;
	return {
		clip: l(a),
		left: l(c)
	};
}
function hr(e, t) {
	e.querySelectorAll("img[data-jav-image]").forEach((e) => {
		let n = e.dataset.javCover || "", r = e.dataset.javThumb || "", i = !!(n && (fr(t) === "cover" || !r)), a = i ? n : r;
		e.classList.toggle("cover", i), e.classList.toggle("whole", i && e.dataset.javImageLayout !== "big"), e.classList.toggle("front", i && e.dataset.javImageLayout === "big"), e.classList.remove("panel"), e.removeAttribute("style"), e.closest(".pic")?.style.removeProperty("--cover-blur"), a && e.getAttribute("src") !== a && (e.src = a);
	});
}
//#endregion
//#region src/islands.ts
var gr = {
	"library-processing": { react: "library-processing" },
	scraping: { react: "scraping" },
	"quality-goals": { react: "quality-goals" },
	configuration: {
		load: an,
		component: on
	},
	activity: { react: "activity" }
}, _r = () => Object.keys(gr), $ = /* @__PURE__ */ new Map();
async function vr(e, t, n, r = {}) {
	let i = gr[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Sr(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	if ($.set(t, a), "react" in i) return br(i, t, n, a, r);
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
			error: jt(e)
		};
	}
	if (!yr(t, a, r)) return;
	let s = {
		...n,
		...o
	};
	ye(F(i.component, s), t);
}
function yr(e, t, n) {
	return $.get(e) === t ? n.isCurrent && !n.isCurrent() ? ($.delete(e), !1) : (e.textContent = "", t.painted = !0, !0) : !1;
}
async function br(e, t, n, r, i) {
	let a = (await import("/dist/peach-react.js")).pages[e.react];
	try {
		await a.prefetch(n, r.controller.signal);
	} catch {
		if (r.controller.signal.aborted) return;
	}
	if (!yr(t, r, i)) return;
	let o = t.ownerDocument.createElement("div");
	o.className = "peach-react", t.append(o);
	let s = a.mount(o, n);
	r.dispose = () => {
		s.unmount(), o.remove();
	};
}
var xr = (e) => !!e && $.has(e);
function Sr(e) {
	for (let t of [...$.keys()]) (t === e || e.contains(t)) && Cr(t);
}
function Cr(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.dispose ? t.dispose() : t.painted && ye(null, e));
}
//#endregion
export { ir as TASTE_GUIDE_KEY, St as activityChartsHtml, Kn as boardPageSkeleton, Se as boundedPreference, Xn as catalogEmptyHtml, Yn as catalogSuggestions, On as clampPage, nr as cleanupSkeletonHtml, er as cloudLocations, tr as cloudPreferenceLocations, vn as createReviewSelection, gt as creatorSankeyHtml, Gn as detailSkeletonHtml, De as distributionChart, Jn as emptyCatalogLayout, In as entitySkeletonHtml, ln as followJobProgress, xn as groupReviewRows, fn as identityEvidenceHtml, je as initBoardControls, xr as islandMounted, _r as islandNames, pr as javImageKind, sn as jobActivityHtml, Ee as jobProgressHtml, An as matchesFaceSource, Pn as mountAvatarPicker, vr as mountIsland, we as mountNumberSetting, jn as nativeImageFit, fr as normalizeJavImage, ur as normalizeJavLayout, dr as normalizeJavPreferences, Dn as pageCount, kn as paginationHtml, mr as panelFrame, be as preferredDirection, ke as radarChart, yt as radialCardHtml, Oe as rankedChart, lr as resourceScanHtml, dn as reviewImageHtml, gn as selectGroup, mn as selectRange, hn as selectionSummary, Zn as sidebarHasCatalogContent, Tt as sidebarSectionHtml, $n as sidebarTagCounts, Te as statCardBody, Ae as syncBoardRange, hr as syncJavImages, Ce as syncNumberSetting, _n as syncSelectionToolbar, Qn as syncSidebarSurface, rr as tasteHistoryGuideHtml, Ot as transitionTheme, Fn as unmountAvatarPicker, Sr as unmountIsland, yn as updateReviewSticky, cn as watchJob, Ct as wireActivityCharts, _t as wireCreatorSankey, Le as wireExpandableRanks, Ie as wireGrowingCharts, bt as wireRadialCards, pn as wireReviewPictures, Tn as wireReviewSelection, Et as wireSidebarGroups, ar as wireTasteHistoryGuide };
