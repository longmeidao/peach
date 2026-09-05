import { emptyStateHtml as e, fieldsetTitle as t, noteHtml as n, setActionBusy as r } from "/js/ui-components.js";
import { LOC as i, fmtDur as a, fmtSize as o } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var s, c, l, u, d, f, p, m, h, g, _, v, y, b, x, S = {}, C = [], w = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, T = Array.isArray;
function E(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ee(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function D(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? s.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return O(e, o, r, i, null);
}
function O(e, t, n, r, i) {
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
		__v: i ?? ++l,
		__i: -1,
		__u: 0
	};
	return i == null && c.vnode != null && c.vnode(a), a;
}
function k(e) {
	return e.children;
}
function A(e, t) {
	this.props = e, this.context = t;
}
function j(e, t) {
	if (t == null) return e.__ ? j(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? j(e) : null;
}
function te(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = E({}, t);
		a.__v = t.__v + 1, c.vnode && c.vnode(a), de(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? j(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, pe(r, a, i), t.__e = t.__ = null, a.__e != n && M(a);
	}
}
function M(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), M(e);
}
function ne(e) {
	(!e.__d && (e.__d = !0) && d.push(e) && !re.__r++ || f != c.debounceRendering) && ((f = c.debounceRendering) || p)(re);
}
function re() {
	try {
		for (var e, t = 1; d.length;) d.length > t && d.sort(m), e = d.shift(), t = d.length, te(e);
	} finally {
		d.length = re.__r = 0;
	}
}
function ie(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || C, v = t.length;
	for (c = ae(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || S, p.__i = d, g = de(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && ge(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = oe(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function ae(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = O(null, o, null, null, null) : T(o) ? o = e.__k[a] = O(k, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = O(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = se(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = j(s)), _e(s, s));
	return r;
}
function oe(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = oe(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = j(e)), t = n.insertBefore(e.__e, t || null));
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
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || w.test(t) ? n : n + "px";
}
function le(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ce(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ce(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(v, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[_] = r[_] : (n[_] = y, e.addEventListener(t, a ? x : b, a)) : e.removeEventListener(t, a ? x : b, a);
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
			if (t[g] == null) t[g] = y++;
			else if (t[g] < n[_]) return;
			return n(c.event ? c.event(t) : t);
		}
	};
}
function de(e, t, n, r, i, a, o, s, l, u) {
	var d, f, p, m, h, g, _, v, y, b, x, S, w, D, O, te, M = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (l = !!(32 & n.__u), a = [s = t.__e = n.__e]), (d = c.__b) && d(t);
	n: if (typeof M == "function") {
		f = o.length;
		try {
			if (y = t.props, b = M.prototype && M.prototype.render, x = (d = M.contextType) && r[d.__c], S = d ? x ? x.props.value : d.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new M(y, S) : (t.__c = p = new A(y, S), p.constructor = M, p.render = ve), x && x.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && M.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = E({}, p.__s)), E(p.__s, M.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && M.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && M.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, S), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, S)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), C.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && o.push(p), s = j(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, S), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = S, p.props = y, p.__P = e, p.__e = !1, w = c.__r, D = 0, b) p.state = p.__s, p.__d = !1, w && w(t), d = p.render(p.props, p.state, p.context), C.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, w && w(t), d = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++D < 25);
			p.state = p.__s, p.getChildContext != null && (r = E(E({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), O = d != null && d.type === k && d.key == null ? me(d.props.children) : d, s = ie(e, T(O) ? O : [O], t, n, r, i, a, o, s, l, u), p.base = t.__e, t.__u &= -161, p.__h.length && o.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (o.length = f, t.__v = null, l || a != null) {
				if (e.then) {
					for (t.__u |= l ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (te = a.length; te--;) ee(a[te]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || fe(t), c.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = he(n.__e, t, n, r, i, a, o, l, u);
	return (d = c.diffed) && d(t), 128 & t.__u ? void 0 : s;
}
function fe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(fe));
}
function pe(e, t, n) {
	for (var r = 0; r < n.length; r++) ge(n[r], n[++r], n[++r]);
	c.__c && c.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			c.__e(e, t.__v);
		}
	});
}
function me(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : T(e) ? e.map(me) : e.constructor === void 0 ? E({}, e) : null;
}
function he(e, t, n, r, i, a, o, l, u) {
	var d, f, p, m, h, g, _, v = n.props || S, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (d = 0; d < a.length; d++) if ((h = a[d]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[d] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), l &&= (c.__m && c.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || l && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && s.call(e.childNodes), !l && a != null) for (v = {}, d = 0; d < e.attributes.length; d++) v[(h = e.attributes[d]).name] = h.value;
		for (d in v) h = v[d], d == "dangerouslySetInnerHTML" ? p = h : d == "children" || d in y || d == "value" && "defaultValue" in y || d == "checked" && "defaultChecked" in y || le(e, d, null, h, i);
		for (d in y) h = y[d], d == "children" ? m = h : d == "dangerouslySetInnerHTML" ? f = h : d == "value" ? g = h : d == "checked" ? _ = h : l && typeof h != "function" || v[d] === h || le(e, d, h, v[d], i);
		if (f) l || p && (f.__html == p.__html || f.__html == e.innerHTML) || (e.innerHTML = f.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), ie(t.type == "template" ? e.content : e, T(m) ? m : [m], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && j(n, 0), l, u), a != null) for (d = a.length; d--;) ee(a[d]);
		l && b != "textarea" || (d = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[d] || b == "progress" && !g || b == "option" && g != v[d]) && le(e, d, g, v[d], i), d = "checked", _ != null && _ != e[d] && le(e, d, _, v[d], i));
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
		c.__e(e, n);
	}
}
function _e(e, t, n) {
	var r, i;
	if (c.unmount && c.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || ge(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			c.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && _e(r[i], t, n || typeof e.type != "function");
	n || ee(e.__e), e.__c = e.__ = e.__e = void 0;
}
function ve(e, t, n) {
	return this.constructor(e, n);
}
function ye(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), c.__ && c.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], de(t, e = (!r && n || t).__k = D(k, null, [e]), i || S, S, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? s.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), pe(a, e, o), e.props.children = null;
}
s = C.slice, c = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, l = 0, u = function(e) {
	return e != null && e.constructor === void 0;
}, A.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = E({}, this.state);
	typeof e == "function" && (e = e(E({}, n), this.props)), e && E(n, e), e != null && this.__v && (t && this._sb.push(t), ne(this));
}, A.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ne(this));
}, A.prototype.render = k, d = [], p = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, m = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, re.__r = 0, h = Math.random().toString(8), g = "__d" + h, _ = "__a" + h, v = /(PointerCapture)$|Capture$/i, y = 0, b = ue(!1), x = ue(!0);
//#endregion
//#region src/api.ts
var be = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, xe = (e) => {
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
}, N = (e) => e instanceof Error ? e.message : String(e);
async function Se(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new be(xe(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function P(e, t, n = "POST", r) {
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
	if (!i.ok) throw new be(xe(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var F, I, Ce, we, Te = 0, Ee = [], L = c, De = L.__b, Oe = L.__r, ke = L.diffed, Ae = L.__c, je = L.unmount, Me = L.__;
function Ne(e, t) {
	L.__h && L.__h(I, e, Te || t), Te = 0;
	var n = I.__H || (I.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function R(e) {
	return Te = 1, Pe(We, e);
}
function Pe(e, t, n) {
	var r = Ne(F++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : We(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = I, !I.__f)) {
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
		I.__f = !0;
		var a = I.shouldComponentUpdate, o = I.componentWillUpdate;
		I.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, I.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function Fe(e, t) {
	var n = Ne(F++, 3);
	!L.__s && Ue(n.__H, t) && (n.__ = e, n.u = t, I.__H.__h.push(n));
}
function Ie(e, t) {
	var n = Ne(F++, 4);
	!L.__s && Ue(n.__H, t) && (n.__ = e, n.u = t, I.__h.push(n));
}
function z(e) {
	return Te = 5, Le(function() {
		return { current: e };
	}, []);
}
function Le(e, t) {
	var n = Ne(F++, 7);
	return Ue(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Re() {
	for (var e; e = Ee.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(Ve), t.__h.some(He), t.__h = [];
		} catch (n) {
			t.__h = [], L.__e(n, e.__v);
		}
	}
}
L.__b = function(e) {
	I = null, De && De(e);
}, L.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Me && Me(e, t);
}, L.__r = function(e) {
	Oe && Oe(e), F = 0;
	var t = (I = e.__c).__H;
	t && (Ce === I ? (t.__h = [], I.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(Ve), t.__h.some(He), t.__h = [], F = 0)), Ce = I;
}, L.diffed = function(e) {
	ke && ke(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Ee.push(t) !== 1 && we === L.requestAnimationFrame || ((we = L.requestAnimationFrame) || Be)(Re)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ce = I = null;
}, L.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(Ve), e.__h = e.__h.filter(function(e) {
				return !e.__ || He(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], L.__e(n, e.__v);
		}
	}), Ae && Ae(e, t);
}, L.unmount = function(e) {
	je && je(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			Ve(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && L.__e(t, n.__v));
};
var ze = typeof requestAnimationFrame == "function";
function Be(e) {
	var t, n = function() {
		clearTimeout(r), ze && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	ze && (t = requestAnimationFrame(n));
}
function Ve(e) {
	var t = I, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), I = t;
}
function He(e) {
	var t = I;
	e.__c = e.__(), I = t;
}
function Ue(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function We(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Ge = 0;
Array.isArray;
function B(e, t, n, r, i, a) {
	t ||= {};
	var o, s, l = t;
	if ("ref" in l) for (s in l = {}, t) s == "ref" ? o = t[s] : l[s] = t[s];
	var u = {
		type: e,
		props: l,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --Ge,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) l[s] === void 0 && (l[s] = o[s]);
	return c.vnode && c.vnode(u), u;
}
//#endregion
//#region src/islands/configuration.tsx
var Ke = "/api/configuration", qe = "/api/pick-folder", Je = 8e3, Ye = (e, t) => Se(Ke, t), V = ({ html: e, class: t }) => /* @__PURE__ */ B("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), Xe = (e) => !(e instanceof be) || e.status !== 400 ? null : e.body?.errors ?? null;
function Ze({ facts: e }) {
	return /* @__PURE__ */ B("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ B("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ B(V, { html: t("configFactsTitle", "运行信息") }), /* @__PURE__ */ B("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ B(k, { children: [/* @__PURE__ */ B("dt", { children: e.term }), /* @__PURE__ */ B("dd", { children: e.value })] }))
			})]
		})
	});
}
function Qe({ data: e, receipt: i }) {
	let [a, o] = R(e.media_dirs.length ? e.media_dirs : [""]), [s, c] = R(String(e.port)), [l, u] = R(!1), [d, f] = R([]), [p, m] = R(""), [h, g] = R(""), [_, v] = R(null), [y, b] = R(null), x = z(!1), S = z(e.revision), C = z([]), w = z(null);
	Ie(() => {
		y !== null && (C.current[y]?.focus(), b(null));
	}, [y]), Fe(() => {
		if (!_) return;
		let e = setTimeout(() => location.assign(_.url), Je);
		return () => clearTimeout(e);
	}, [_]);
	let T = (e, t) => {
		o((n) => n.map((n, r) => r === e ? t : n));
	}, E = () => {
		b(a.length), o((e) => [...e, ""]);
	}, ee = (e) => {
		o((t) => t.filter((t, n) => n !== e)), f((t) => t.filter((t, n) => n !== e));
	}, D = (e, t) => {
		f((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, O = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			r(t, !0);
			try {
				let { path: t } = await P(qe, { initial: a[e] ?? "" });
				t && (T(e, t), D(e, ""));
			} catch (t) {
				D(e, N(t));
			} finally {
				r(t, !1);
			}
		}
	};
	return _ ? /* @__PURE__ */ B("div", {
		class: "configsaved",
		role: "status",
		children: [/* @__PURE__ */ B(V, { html: n("配置已保存，Peach 正在重新启动。", {
			variant: "success",
			label: "已保存"
		}) }), /* @__PURE__ */ B("p", {
			class: "confighelp",
			children: [
				"几秒后自动打开新地址；没跳转就点 ",
				/* @__PURE__ */ B("a", {
					href: _.url,
					children: "进入馆藏"
				}),
				"。"
			]
		})]
	}) : /* @__PURE__ */ B("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (e) => {
			if (e.preventDefault(), !x.current) {
				x.current = !0, r(w.current, !0), g("");
				try {
					let e = await P(Ke, {
						revision: S.current,
						media_dirs: a,
						port: s,
						scan_now: l
					});
					S.current = e.revision, f([]), m(""), i("已保存配置"), v(e);
				} catch (e) {
					let t = Xe(e);
					t ? (f(t.media_dirs ?? []), m(t.port ?? "")) : (f([]), m(""), g(N(e)));
				} finally {
					x.current = !1, r(w.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ B("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ B(V, { html: t("configTitle", "这台电脑") }),
				/* @__PURE__ */ B("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ B("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ B("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: a.map((e, t) => /* @__PURE__ */ B("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ B("input", {
										class: "geist-input",
										type: "text",
										value: e,
										"aria-label": `媒体文件夹 ${t + 1}`,
										"aria-invalid": d[t] ? "true" : void 0,
										onInput: (e) => T(t, e.currentTarget.value),
										ref: (e) => {
											C.current[t] = e;
										}
									}),
									/* @__PURE__ */ B("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => O(t, e.currentTarget),
										children: /* @__PURE__ */ B("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ B("use", { href: "#i-folder-search" })
										})
									}),
									a.length > 1 ? /* @__PURE__ */ B("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => ee(t),
										children: /* @__PURE__ */ B("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ B("use", { href: "#i-x" })
										})
									}) : null,
									d[t] ? /* @__PURE__ */ B("p", {
										class: "configbad",
										role: "alert",
										children: d[t]
									}) : null
								]
							}, t))
						}),
						/* @__PURE__ */ B("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: E,
							children: "添加文件夹"
						}),
						/* @__PURE__ */ B("p", {
							class: "confighelp",
							children: "Peach 从这些文件夹读取视频和图片。可以是外置硬盘上的文件夹，但必须已经存在。"
						})
					]
				}),
				/* @__PURE__ */ B("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ B("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ B("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: s,
							"aria-invalid": p ? "true" : void 0,
							onInput: (e) => c(e.currentTarget.value)
						}),
						p ? /* @__PURE__ */ B("p", {
							class: "configbad",
							role: "alert",
							children: p
						}) : null,
						/* @__PURE__ */ B("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ B("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ B("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ B("input", {
							type: "checkbox",
							checked: l,
							onChange: (e) => u(e.currentTarget.checked)
						}), /* @__PURE__ */ B("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ B("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ B("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ B("span", { children: "保存后扫描媒体文件夹" })]
				}),
				h ? /* @__PURE__ */ B(V, { html: n(h, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ B("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ B("p", { children: "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ B("button", {
				type: "submit",
				class: "geist-button primary",
				ref: w,
				children: "保存配置"
			})]
		})]
	});
}
function $e({ receipt: e, data: t, error: r }) {
	return r || !t ? /* @__PURE__ */ B(V, {
		class: "configpage",
		html: n(r || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ B("div", {
		class: "configpage",
		children: [t.editable ? /* @__PURE__ */ B(Qe, {
			data: t,
			receipt: e
		}) : /* @__PURE__ */ B(V, { html: n(t.notice, {
			variant: "secondary",
			label: "只读"
		}) }), /* @__PURE__ */ B(Ze, { facts: t.facts })]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var et = Symbol.for("preact-signals");
function tt() {
	if (G > 1) G--;
	else {
		var e, t = !1;
		for ((function() {
			var e = ot;
			for (ot = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); W !== void 0;) {
			var n = W;
			for (W = void 0, K++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && ut(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (K = 0, G--, t) throw e;
	}
}
function nt(e) {
	if (G > 0) return e();
	at = ++it, G++;
	try {
		return e();
	} finally {
		tt();
	}
}
var H, U = void 0;
function rt(e) {
	var t = U, n = H;
	U = void 0, H = void 0;
	try {
		return e();
	} finally {
		U = t, H = n;
	}
}
var W = void 0, G = 0, K = 0, it = 0, at = 0, ot = void 0, st = 0;
function ct(e) {
	if (U !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== U) return t = {
			i: 0,
			S: e,
			p: U.s,
			n: void 0,
			t: U,
			e: void 0,
			x: void 0,
			r: t
		}, U.s !== void 0 && (U.s.n = t), U.s = t, e.n = t, 32 & U.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = U.s, t.n = void 0, U.s.n = t, U.s = t), t;
	}
}
function q(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
q.prototype.brand = et, q.prototype.h = function() {
	return !0;
}, q.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? rt(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, q.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && rt(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, q.prototype.subscribe = function(e) {
	var t = this;
	return X(function() {
		var n = t.value;
		rt(function() {
			return e(n);
		});
	}, { name: "sub" });
}, q.prototype.valueOf = function() {
	return this.value;
}, q.prototype.toString = function() {
	return this.value + "";
}, q.prototype.toJSON = function() {
	return this.value;
}, q.prototype.peek = function() {
	var e = this;
	return rt(function() {
		return e.value;
	});
}, Object.defineProperty(q.prototype, "value", {
	get: function() {
		var e = ct(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (K > 100) throw Error("Cycle detected");
			(function(e) {
				G !== 0 && K === 0 && e.l !== at && (e.l = at, ot = {
					S: e,
					v: e.v,
					i: e.i,
					o: ot
				});
			})(this), this.v = e, this.i++, st++, G++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				tt();
			}
		}
	}
});
function lt(e, t) {
	return new q(e, t);
}
function ut(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function dt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function ft(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function J(e, t) {
	q.call(this, void 0, t), this.x = e, this.s = void 0, this.g = st - 1, this.f = 4;
}
J.prototype = new q(), J.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === st)) return !0;
	if (this.g = st, this.f |= 1, this.i > 0 && !ut(this)) return this.f &= -2, !0;
	var e = U;
	try {
		dt(this), U = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return U = e, ft(this), this.f &= -2, !0;
}, J.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	q.prototype.S.call(this, e);
}, J.prototype.U = function(e) {
	if (this.t !== void 0 && (q.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, J.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(J.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = ct(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function pt(e, t) {
	return new J(e, t);
}
function mt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		G++;
		var n = U;
		U = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, ht(e), t;
		} finally {
			U = n, tt();
		}
	}
}
function ht(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, mt(e);
}
function gt(e) {
	if (U !== this) throw Error("Out-of-order effect");
	ft(this), U = e, this.f &= -2, 8 & this.f && ht(this), tt();
}
function Y(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, H && H.push(this);
}
Y.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Y.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, mt(this), dt(this), G++;
	var e = U;
	return U = this, gt.bind(this, e);
}, Y.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = W, W = this);
}, Y.prototype.d = function() {
	this.f |= 8, 1 & this.f || ht(this);
}, Y.prototype.dispose = function() {
	this.d();
};
function X(e, t) {
	var n = new Y(e, t);
	try {
		n.c();
	} catch (e) {
		throw n.d(), e;
	}
	var r = n.d.bind(n);
	return r[Symbol.dispose] = r, r;
}
//#endregion
//#region node_modules/@preact/signals/dist/signals.module.js
var _t, vt, yt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, bt = [];
X(function() {
	_t = this.N;
})();
function Z(e, t) {
	c[e] = t.bind(null, c[e] || function() {});
}
function xt(e) {
	if (vt) {
		var t = vt;
		vt = void 0, t();
	}
	vt = e && e.S();
}
function St(e) {
	var t = this, n = e.data, r = wt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Le(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = pt(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = pt(function() {
			return !Array.isArray(i.value) && !u(i.value);
		}), o = X(function() {
			if (this.N = Dt, a.value) {
				var t = i.value;
				e.__v && e.__v.__e && e.__v.__e.nodeType === 3 && (e.__v.__e.data = t);
			}
		}), s = t.__$u.d;
		return t.__$u.d = function() {
			o(), s.call(this);
		}, [a, i];
	}, []), a = i[0], o = i[1];
	return a.value ? o.peek() : o.value;
}
St.displayName = "ReactiveTextNode", Object.defineProperties(q.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: St
	},
	props: {
		configurable: !0,
		get: function() {
			var e = this;
			return { data: { get value() {
				return e.value;
			} } };
		}
	},
	__b: {
		configurable: !0,
		value: 1
	}
}), Z("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof q && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Z("__r", function(e, t) {
	if (e(t), t.type !== k) {
		xt();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return X(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				yt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), xt(n);
	}
}), Z("__e", function(e, t, n, r) {
	xt(), e(t, n, r);
}), Z("diffed", function(e, t) {
	xt();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Ct(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Ct(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = lt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: X(function() {
			this.N = Dt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Z("unmount", function(e, t) {
	if (typeof t.type == "string") {
		var n = t.__e;
		if (n) {
			var r = n.U;
			if (r) for (var i in n.U = void 0, r) {
				var a = r[i];
				a && a.d();
			}
		}
		var o = t.__np;
		if (o) {
			var s = t.props;
			for (var c in o) s[c] = o[c];
		}
		t.__np = void 0;
	} else {
		var l = t.__c;
		if (l) {
			var u = l.__$u;
			u && (l.__$u = void 0, u.d());
		}
	}
	e(t);
}), Z("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), A.prototype.shouldComponentUpdate = function(e, t) {
	if (this.__R) return !0;
	var n = this.__$u, r = n && n.s !== void 0;
	for (var i in t) return !0;
	if (this.__f || typeof this.u == "boolean" && !0 === this.u) {
		var a = 2 & this.__$f;
		if (!(r || a || 4 & this.__$f) || 1 & this.__$f) return !0;
	} else if (!(r || 4 & this.__$f) || 3 & this.__$f) return !0;
	for (var o in e) if (o !== "__source" && e[o] !== this.props[o]) return !0;
	for (var s in this.props) if (!(s in e)) return !0;
	return !1;
};
function wt(e, t) {
	return Le(function() {
		return lt(e, t);
	}, []);
}
var Tt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Et() {
	nt(function() {
		for (var e; e = bt.shift();) _t.call(e);
	});
}
function Dt() {
	bt.push(this) === 1 && (c.requestAnimationFrame || Tt)(Et);
}
//#endregion
//#region src/state/quality-goals.ts
var Ot = "/api/quality-goals?limit=200", kt = {
	data: null,
	error: ""
}, Q = lt(kt), At = 0, jt = pt(() => Q.value);
pt(() => Q.value.data?.total ?? null);
function Mt() {
	At += 1, Q.value = kt;
}
async function Nt(e) {
	let t = At += 1;
	try {
		let n = await Se(Ot, e);
		return t === At && (Q.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === At && (Q.value = {
			data: null,
			error: N(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Pt = (e, t) => Nt(t), Ft = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function It({ openItem: t, javTitleHtml: r, javDisplayName: s, srcBadge: c }) {
	let { data: l, error: u } = jt.value;
	if (u) return /* @__PURE__ */ B("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: n(u, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = l?.items ?? [];
	return d.length ? /* @__PURE__ */ B("div", {
		class: "qualitylist",
		children: d.map((e) => /* @__PURE__ */ B("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ B("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${s(e)}`,
				onClick: () => t(e.id),
				children: /* @__PURE__ */ B("img", {
					src: Ft(e),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ B("div", { children: [
				/* @__PURE__ */ B("h3", { children: /* @__PURE__ */ B("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(e.id),
					dangerouslySetInnerHTML: { __html: r(e) }
				}) }),
				/* @__PURE__ */ B("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ B("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: c(e.location, e.cost) }
						}),
						/* @__PURE__ */ B("span", { children: i[e.location] ?? e.location }),
						/* @__PURE__ */ B("span", { children: a(e.duration) }),
						/* @__PURE__ */ B("span", { children: o(e.size ?? 0) })
					]
				}),
				e.reason ? /* @__PURE__ */ B("p", { children: e.reason }) : null
			] })]
		}, e.id))
	}) : /* @__PURE__ */ B("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: e("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function Lt(e) {
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
function Rt(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	Lt({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (e.title || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
				t.innerHTML = e.container ? e.container(c) : c;
			} else if (r && r === a.job_id) r = void 0, i = !0, e.host.hidden = a.status !== "failed", sessionStorage.removeItem(n), t.innerHTML = a.status === "failed" ? e.note(a.error || "检查失败") : "", e.complete(a);
			else {
				if (r && a.status === "idle") {
					e.host.hidden = !1, t.innerHTML = e.note("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(n), i = !0;
					return;
				}
				t.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, t.innerHTML = e.note("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/islands/scraping.tsx
var zt = (e, t) => Se("/api/scraping", t);
function Bt({ source: e, toast: i }) {
	let [a, o] = R(e), [s, c] = R(e.network), [l, u] = R(""), [d, f] = R(""), [p, m] = R(""), [h, g] = R(!1), [_, v] = R(""), [y, b] = R([]), x = z(null), S = z(null);
	Ie(() => {
		S.current?.querySelectorAll("button").forEach((e) => r(e, h));
	}, [h]);
	let C = z(new AbortController());
	Fe(() => () => C.current.abort(), []);
	async function w(t) {
		if (!h) {
			g(!0), v(""), b([]);
			try {
				if (t === "check") {
					let t = await P("/api/scraping/check", { source: e.source }, "POST", C.current.signal);
					C.current.signal.aborted || b(t.results);
				} else {
					let n = await P("/api/scraping/settings", {
						source: e.source,
						network: s,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: t === "revoke"
					}, "POST", C.current.signal);
					C.current.signal.aborted || (o(n.saved), u(""), f(""), m(""), x.current && (x.current.value = ""), i(t === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				C.current.signal.aborted || v(N(e));
			} finally {
				C.current.signal.aborted || g(!1);
			}
		}
	}
	return /* @__PURE__ */ B("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ B("form", {
			ref: S,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), w("save");
			},
			children: [/* @__PURE__ */ B("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ B("div", { dangerouslySetInnerHTML: { __html: t(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ B("label", { children: ["连接方式", /* @__PURE__ */ B("select", {
						class: "geist-input",
						value: s,
						disabled: h,
						onChange: (e) => c(e.currentTarget.value),
						children: [
							/* @__PURE__ */ B("option", {
								value: "environment",
								children: "环境代理"
							}),
							/* @__PURE__ */ B("option", {
								value: "direct",
								children: "应用直连"
							}),
							/* @__PURE__ */ B("option", {
								value: "proxy",
								children: "指定代理"
							})
						]
					})] }),
					s === "proxy" && /* @__PURE__ */ B("label", { children: ["代理地址", /* @__PURE__ */ B("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: a.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: h,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ B(k, { children: [
						/* @__PURE__ */ B("p", { children: [
							/* @__PURE__ */ B("a", {
								href: e.login,
								target: "_blank",
								rel: "noopener noreferrer",
								children: "打开官网登录"
							}),
							" · ",
							a.cookie_saved ? "Cookie 已保存，尚未验证会话" : "尚未提供 Cookie"
						] }),
						/* @__PURE__ */ B("label", { children: ["Cookie 请求头", /* @__PURE__ */ B("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: h || !!p,
							onInput: (e) => f(e.currentTarget.value)
						})] }),
						/* @__PURE__ */ B("label", { children: ["Netscape Cookie 文件", /* @__PURE__ */ B("input", {
							class: "geist-input",
							ref: x,
							type: "file",
							accept: ".txt",
							disabled: h || !!d,
							onChange: async (e) => {
								let t = e.currentTarget.files?.[0];
								if (!t) {
									m("");
									return;
								}
								if (m(""), t.size > 262144) {
									v("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
									return;
								}
								g(!0);
								try {
									let e = await t.text();
									C.current.signal.aborted || m(e);
								} catch {
									C.current.signal.aborted || v("Cookie 文件未读取，请重新选择");
								} finally {
									C.current.signal.aborted || g(!1);
								}
							}
						})] })
					] }),
					_ && /* @__PURE__ */ B("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: n(_, { variant: "error" }) }
					}),
					y.map((e) => /* @__PURE__ */ B("p", {
						role: "status",
						children: [
							e.label,
							"：",
							e.ok ? "可连接" : "未取得",
							e.width ? ` · ${e.width} × ${e.height}` : "",
							e.message ? ` · ${e.message}` : ""
						]
					}, e.label))
				]
			}), /* @__PURE__ */ B("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ B("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ B("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void w("check"),
						children: "检查已保存的连接"
					}),
					e.accepts_cookie && a.cookie_saved && /* @__PURE__ */ B("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void w("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function Vt({ data: e, error: i, toast: a }) {
	let [o, s] = R(""), [c, l] = R(!1), [u, d] = R(""), f = z(null);
	Ie(() => r(f.current, c), [c]);
	let p = z(new AbortController()), m = z(0);
	async function h(e = !1) {
		let t = ++m.current;
		await Lt({
			read: (e) => Se("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && a(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Fe(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!c) {
			m.current++, l(!0), d("");
			try {
				await P("/api/scraping/cover", { code: o }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(N(e)));
			}
		}
	}
	return i ? /* @__PURE__ */ B("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: n(i, { variant: "error" }) }
	}) : /* @__PURE__ */ B("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ B("p", { children: "高清来源可能需要代理。环境代理读取服务进程的代理环境变量；应用直连仍可能经过系统隧道。" }),
			/* @__PURE__ */ B("p", { children: "封面采集保留最高可得画质，失败保留已有图片。连接检查不验证登录会话。" }),
			/* @__PURE__ */ B("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ B("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ B("div", { dangerouslySetInnerHTML: { __html: t("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ B("form", {
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ B("label", { children: ["馆藏番号", /* @__PURE__ */ B("input", {
								class: "geist-input",
								required: !0,
								value: o,
								disabled: c,
								placeholder: "ABW-232",
								onInput: (e) => s(e.currentTarget.value)
							})] }), /* @__PURE__ */ B("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取或升级封面"
							})]
						}),
						u && /* @__PURE__ */ B("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: n(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ B(Bt, {
				source: e,
				toast: a
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var Ht = { "quality-goals": {
	refresh: Nt,
	reset: Mt
} }, Ut = () => Object.keys(Ht);
async function Wt(e) {
	let t = Ht[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/sidebar.ts
function Gt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Kt(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function qt(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/islands.ts
var Jt = {
	scraping: {
		load: zt,
		component: Vt
	},
	"quality-goals": {
		load: Pt,
		component: It
	},
	configuration: {
		load: Ye,
		component: $e
	}
}, Yt = () => Object.keys(Jt), $ = /* @__PURE__ */ new Map();
async function Xt(e, t, n, r = {}) {
	let i = Jt[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Zt(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$.set(t, a);
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
			error: N(e)
		};
	}
	if ($.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	ye(D(i.component, s), t);
}
function Zt(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && ye(null, e));
}
//#endregion
export { Rt as followJobProgress, Yt as islandNames, Xt as mountIsland, Wt as refreshStore, Gt as sidebarHasCatalogContent, qt as sidebarTagCounts, Ut as storeNames, Kt as syncSidebarSurface, Zt as unmountIsland, Lt as watchJob };
