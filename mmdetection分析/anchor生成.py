import torch

class AnchorGenerator(object):
	def __init__(self, base_size, scales, ratios, scale_major=True, ctr=None):
		self.base_size = base_size
		self.scales = torch.Tensor(scales)
		self.ratios = torch.Tensor(ratios)
		self.scale_major = scale_major
		self.crt = ctr
		self.base_anchors = self.gen_base_anchors()

	@property
	def num_base_anchors(self):
		return self.base_anchors.size(0)

	def gen_base_anchors(self):
		w = self.base_size
		h = self.base_size
		if self.crt is None:
			x_ctr = 0.5 * (w - 1)
			y_ctr = 0.5 * (h - 1)
		else:
			x_ctr, y_ctr = self.crt

		h_ratio = torch.sqrt(self.ratios)
		w_ratio = 1 / h_ratio
		if self.scale_major:
			ws = (w * w_ratio[:, None] * self.scales[None, :]).view(-1)
			hs = (h * h_ratio[:, None] * self.scales[None, :]).view(-1)
		else:
			ws = (w * self.scales[:, None] * w_ratio[None, :]).view(-1)
			hs = (h * self.scales[:, None] * h_ratio[None, :]).view(-1)

		base_anchors = torch.stack(
			[
				x_ctr - 0.5 * (ws - 1), y_ctr - 0.5 * (hs - 1),
				x_ctr + 0.5 * (ws - 1), y_ctr + 0.5 * (hs - 1)
			],
			dim=-1).round()

		return base_anchors

	def _meshgrid(self, x, y, row_major=True):
		xx = x.repeat(len(y))
		yy = y.view(-1, 1).repeat(1, len(x)).view(-1)
		if row_major:
			return xx, yy
		else:
			return yy, xx
	
	def grid_anchor(self, featmap_size, stride=16 , device='cuda'):
		base_anchors = self.base_anchors.to(device)

		feat_h, feat_w = featmap_size
		shift_x = torch.arange(0, feat_w, device=device) * stride
		shift_y = torch.arange(0, feat_h, device=device) * stride
		shift_xx, shift_yy = self._meshgrid(shift_x, shift_y)
		shifts = torch.stack([shift_xx, shift_yy, shift_xx, shift_yy], dim=-1)
		shifts = shifts.type_as(base_anchors)

		all_anchors = base_anchors[None, :, :] + shift[:, None, :]
		all_anchors = all_anchors.view(-1, 4)

		return all_anchors

	def valid_flags(self, featmap_size, valid_size, device='cuda'):
		feat_h, feat_w = featmap_size
		valid_h, valid_w = valid_size
		assert valid_h <= feat_h and valid_w <= feat_w
		valid_x = torch.zeros(feat_w, dtype=torch.uint8, device=device)
		valid_y = torch.zeros(feat_h, dtype=torch.uint8, device=device)
		valid_x[:valid_w] = 1
		valid_y[:valid_h] = 1
		valid_xx, valid_yy = self._meshgrid(valid_x, valid_y)
		valid = valid_xx & valid_yy
		valid = valid[:, None].expand(valid.size(0), self.num_base_anchors).contiguous.view(-1)
		return valid

		

	
		